import os
import time
import sqlite3
import requests
import threading
import re
from queue import Queue
from openai import OpenAI
from flask import Flask, jsonify

# ================= CONFIG =================
BALE_TOKEN = os.getenv("BALE_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "586110315"))

BASE_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

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
banned INTEGER DEFAULT 0,
state TEXT DEFAULT ''
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS memory(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
role TEXT,
content TEXT,
ts INTEGER
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

threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000), daemon=True).start()

# ================= CORE =================
task_queue = Queue()
spam = {}

CARD = "1010202030304040"

# ================= SEND =================
def send(chat_id, text, reply_to=None):
    data = {"chat_id": chat_id, "text": text[:4000]}
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

def update_last(uid, now):
    cur.execute("UPDATE users SET last_message=? WHERE user_id=?", (now, uid))
    db.commit()

def set_ban(uid, val):
    cur.execute("UPDATE users SET banned=? WHERE user_id=?", (val, uid))
    db.commit()

def set_state(uid, state):
    cur.execute("UPDATE users SET state=? WHERE user_id=?", (state, uid))
    db.commit()

# ================= MEMORY =================
def save_memory(uid, role, content):
    cur.execute("""
        INSERT INTO memory(user_id,role,content,ts)
        VALUES(?,?,?,?)
    """, (uid, role, content, int(time.time())))
    db.commit()

def load_memory(uid, limit=6):
    cur.execute("""
        SELECT role,content FROM memory
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT ?
    """, (uid, limit))
    rows = cur.fetchall()
    rows.reverse()
    return [{"role": r, "content": c} for r, c in rows]

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
    if now - last < 3:
        return False
    spam[key] = now
    return True

# ================= AI =================
def ask_ai(uid, text):
    messages = [
        {
            "role": "system",
            "content": "تو موری هستی، یک دستیار فارسی هوشمند، کوتاه، دقیق و کاربردی. اگر لازم نبود توضیح اضافه نده."
        }
    ]

    messages += load_memory(uid, 6)
    messages.append({"role": "user", "content": text})

    res = client.chat.completions.create(
        model="Qwen/Qwen3-8B",
        messages=messages,
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

            save_memory(uid, "user", text)
            save_memory(uid, "assistant", reply)

        except Exception as e:
            print("AI ERROR:", e)
            send(chat_id, "خطا", reply_to=msg_id)

        task_queue.task_done()

threading.Thread(target=worker, daemon=True).start()

# ================= MAIN =================
print("MORI PRO 3 RUNNING")

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

            if not text:
                continue

            vip, last, banned, state = get_user(uid)
            now = int(time.time())

            if banned:
                continue

            if uid != ADMIN_ID and now - last < 2:
                continue

            update_last(uid, now)

            # ================= GROUP FILTER =================
            if msg["chat"]["type"] != "private":
                if not is_calling_mori(msg, text):
                    continue
                if not anti_spam(uid, chat_id, now):
                    continue

            # ================= VIP STATE (PAYMENT SIMPLE) =================
            if state.startswith("vip_"):
                cur.execute("""
                    INSERT INTO payments(user_id,plan,tracking)
                    VALUES(?,?,?)
                """, (uid, state, text))
                db.commit()

                set_state(uid, "")

                send(chat_id, "✅ پرداخت ثبت شد", reply_to=msg_id)
                continue

            # ================= QUEUE =================
            task_queue.put((uid, chat_id, msg_id, text))

    except Exception as e:
        print("ERR:", e)
        time.sleep(2)
