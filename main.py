import os
import time
import sqlite3
import requests
import threading
import re
from queue import Queue
from collections import defaultdict, deque
from openai import OpenAI
from flask import Flask, jsonify

# ================= CONFIG =================
BALE_TOKEN = os.getenv("BALE_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "586110315"))

BASE_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"
CARD = "1010202030304040"

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

# ================= DB =================
db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
vip_until INTEGER DEFAULT 0,
last_message INTEGER DEFAULT 0,
state TEXT DEFAULT '',
banned INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS payments(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
plan TEXT,
tracking TEXT,
status INTEGER DEFAULT 0,
amount INTEGER DEFAULT 0,
paid_at INTEGER DEFAULT 0
)
""")

db.commit()

# ================= FLASK =================
app = Flask(__name__)

@app.route("/api/stats")
def stats():
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM payments")
    payments = cur.fetchone()[0]

    cur.execute("SELECT SUM(amount) FROM payments WHERE status=1")
    revenue = cur.fetchone()[0] or 0

    return jsonify({
        "users": users,
        "payments": payments,
        "revenue": revenue
    })

def run_api():
    app.run(host="0.0.0.0", port=5000)

# ================= BOT STATE =================
memory = defaultdict(lambda: deque(maxlen=6))
spam = {}
task_queue = Queue()

# ================= SEND =================
def send(chat_id, text, reply_to=None):
    data = {
        "chat_id": chat_id,
        "text": text[:4000],
    }
    if reply_to:
        data["reply_to_message_id"] = reply_to

    requests.post(f"{BASE_URL}/sendMessage", json=data)

# ================= USER =================
def get_user(uid):
    cur.execute("SELECT vip_until,last_message,banned,state FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO users(user_id) VALUES(?)", (uid,))
        db.commit()
        return (0, 0, 0, "")
    return row

def set_state(uid, state):
    cur.execute("UPDATE users SET state=? WHERE user_id=?", (state, uid))
    db.commit()

def set_ban(uid, val):
    cur.execute("UPDATE users SET banned=? WHERE user_id=?", (val, uid))
    db.commit()

def set_vip(uid, days):
    now = int(time.time())
    cur.execute("SELECT vip_until FROM users WHERE user_id=?", (uid,))
    old = cur.fetchone()[0] or 0
    new = max(now, old) + days * 86400
    cur.execute("UPDATE users SET vip_until=? WHERE user_id=?", (new, uid))
    db.commit()

def update_last(uid, now):
    cur.execute("UPDATE users SET last_message=? WHERE user_id=?", (now, uid))
    db.commit()

# ================= MORI DETECTOR =================
def is_calling_mori(msg, text):
    chat_type = msg["chat"]["type"]

    if chat_type == "private":
        return True

    t = text.lower()

    if msg.get("reply_to_message"):
        return True

    for e in msg.get("entities", []):
        if e.get("type") == "mention":
            return True

    patterns = [
        r"\bموری\b",
        r"\bmori\b",
        r"@mori",
        r"هی موری",
        r"موری جان",
        r"سلام موری",
        r"موری کمک",
    ]

    return any(re.search(p, t) for p in patterns)

# ================= ANTI SPAM =================
def anti_spam(uid, chat_id, now):
    key = f"{uid}:{chat_id}"
    last = spam.get(key, 0)

    if now - last < 4:
        return False

    spam[key] = now
    return True

# ================= MEMORY =================
def add_memory(uid, user_text, bot_text):
    memory[uid].append({"u": user_text, "b": bot_text})

def build_messages(uid, text):
    msgs = [
        {"role": "system", "content": "تو موری هستی، دستیار فارسی هوشمند، کوتاه و مفید و دوستانه."}
    ]

    for m in memory[uid]:
        msgs.append({"role": "user", "content": m["u"]})
        msgs.append({"role": "assistant", "content": m["b"]})

    msgs.append({"role": "user", "content": text})
    return msgs

# ================= AI =================
def ask_ai(uid, text):
    res = client.chat.completions.create(
        model="Qwen/Qwen3-8B",
        messages=build_messages(uid, text),
        max_tokens=300
    )
    return res.choices[0].message.content

# ================= WORKER =================
def worker():
    while True:
        uid, chat_id, msg_id, text = task_queue.get()

        try:
            reply = ask_ai(uid, text)
            send(chat_id, reply, reply_to=msg_id)
            add_memory(uid, text, reply)

        except Exception as e:
            print("AI ERROR:", e)
            send(chat_id, "خطا", reply_to=msg_id)

        task_queue.task_done()

threading.Thread(target=worker, daemon=True).start()

# ================= API =================
threading.Thread(target=run_api, daemon=True).start()

# ================= MAIN LOOP =================
print("MORI PRO 2 RUNNING")

offset = 0

while True:
    try:
        data = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": offset, "timeout": 30}
        ).json()

        for upd in data.get("result", []):
            offset = upd["update_id"] + 1

            if "message" not in upd:
                continue

            msg = upd["message"]
            uid = msg["from"]["id"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")
            msg_id = msg.get("message_id")

            vip, last, banned, state = get_user(uid)
            now = int(time.time())

            if banned:
                continue

            if uid != ADMIN_ID and now - last < 2:
                continue

            update_last(uid, now)

            if not text:
                continue

            # VIP payment state
            if state and text:
                cur.execute("""
                    INSERT INTO payments(user_id,plan,tracking)
                    VALUES(?,?,?)
                """, (uid, state, text))
                db.commit()

                set_vip(uid, {"vip_1":1,"vip_7":7,"vip_30":30}.get(state, 0))
                set_state(uid, "")

                send(chat_id, "✅ VIP فعال شد", reply_to=msg_id)
                continue

            # ================= MORI SMART FILTER =================
            chat_type = msg["chat"]["type"]

            if chat_type != "private":
                if not is_calling_mori(msg, text):
                    continue

                if not anti_spam(uid, chat_id, now):
                    continue

            # ================= QUEUE AI =================
            task_queue.put((uid, chat_id, msg_id, text))

    except Exception as e:
        print("ERR:", e)
        time.sleep(2)
