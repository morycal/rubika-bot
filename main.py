import os
import time
import sqlite3
import requests
import threading
import re
from queue import PriorityQueue
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
credits INTEGER DEFAULT 20,
last_message INTEGER DEFAULT 0,
banned INTEGER DEFAULT 0,
persona TEXT DEFAULT 'normal'
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS memory(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
content TEXT,
summary INTEGER DEFAULT 0,
ts INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS logs(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
action TEXT,
ts INTEGER
)
""")

db.commit()

# ================= WEB PANEL =================
app = Flask(__name__)

@app.route("/api/stats")
def stats():
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.execute("SELECT SUM(credits) FROM users")
    credits = cur.fetchone()[0] or 0

    return jsonify({
        "users": users,
        "total_credits": credits
    })

threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000), daemon=True).start()

# ================= CORE =================
queue = PriorityQueue()
spam = {}

# ================= SEND =================
def send(chat_id, text, reply_to=None):
    data = {"chat_id": chat_id, "text": text[:4000]}
    if reply_to:
        data["reply_to_message_id"] = reply_to
    requests.post(f"{BASE_URL}/sendMessage", json=data)

# ================= USER =================
def get_user(uid):
    cur.execute("SELECT vip_until,credits,last_message,banned,persona FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO users(user_id) VALUES(?)", (uid,))
        db.commit()
        return (0, 20, 0, 0, "normal")
    return row

def update_user(uid, **kwargs):
    for k, v in kwargs.items():
        cur.execute(f"UPDATE users SET {k}=? WHERE user_id=?", (v, uid))
    db.commit()

# ================= LOG =================
def log(uid, action):
    cur.execute("INSERT INTO logs(user_id,action,ts) VALUES(?,?,?)", (uid, action, int(time.time())))
    db.commit()

# ================= MORI DETECTOR =================
def is_calling_mori(msg, text):
    if msg["chat"]["type"] == "private":
        return True

    t = text.lower()

    if msg.get("reply_to_message"):
        return True

    for e in msg.get("entities", []):
        if e.get("type") == "mention":
            return True

    return bool(re.search(r"\b(موری|mori|@mori)\b|هی موری|موری جان", t))

# ================= ANTI SPAM =================
def anti_spam(uid, chat_id):
    now = time.time()
    key = f"{uid}:{chat_id}"
    last = spam.get(key, 0)

    if now - last < 3:
        return False

    spam[key] = now
    return True

# ================= PERSONA =================
def persona_prompt(p):
    if p == "funny":
        return "تو موری هستی، شوخ و دوستانه جواب بده."
    if p == "strict":
        return "تو موری هستی، رسمی و کوتاه و جدی جواب بده."
    return "تو موری هستی، هوشمند و مفید و متعادل جواب بده."

# ================= MEMORY =================
def save_memory(uid, text):
    cur.execute("INSERT INTO memory(user_id,content,ts) VALUES(?,?,?)", (uid, text, int(time.time())))
    db.commit()

def load_memory(uid):
    cur.execute("SELECT content FROM memory WHERE user_id=? ORDER BY id DESC LIMIT 6", (uid,))
    rows = cur.fetchall()
    return [r[0] for r in reversed(rows)]

def summarize_if_needed(uid):
    cur.execute("SELECT COUNT(*) FROM memory WHERE user_id=?", (uid,))
    c = cur.fetchone()[0]
    if c > 30:
        cur.execute("DELETE FROM memory WHERE user_id=? AND id IN (SELECT id FROM memory WHERE user_id=? LIMIT 10)", (uid, uid))
        db.commit()

# ================= AI =================
def ask_ai(uid, text, persona):
    messages = [{"role": "system", "content": persona_prompt(persona)}]

    for m in load_memory(uid):
        messages.append({"role": "user", "content": m})

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
        priority, data = queue.get()
        uid, chat_id, msg_id, text = data

        try:
            vip_until, credits, last, banned, persona = get_user(uid)

            if credits <= 0:
                send(chat_id, "❌ اعتبار تمام شده", reply_to=msg_id)
                continue

            reply = ask_ai(uid, text, persona)

            update_user(uid, credits=credits-1)

            send(chat_id, reply, reply_to=msg_id)

            save_memory(uid, text)
            save_memory(uid, reply)

            summarize_if_needed(uid)

        except Exception as e:
            print("AI ERROR:", e)
            send(chat_id, "خطا", reply_to=msg_id)

        queue.task_done()

threading.Thread(target=worker, daemon=True).start()

# ================= MAIN =================
print("MORI PRO 4 RUNNING")

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

            vip, credits, last, banned, persona = get_user(uid)

            if banned:
                continue

            if uid != ADMIN_ID and time.time() - last < 2:
                continue

            update_user(uid, last_message=int(time.time()))

            # ================= GROUP FILTER =================
            if msg["chat"]["type"] != "private":
                if not is_calling_mori(msg, text):
                    continue
                if not anti_spam(uid, chat_id):
                    continue

            # ================= ADMIN =================
            if text == "/admin" and uid == ADMIN_ID:
                send(chat_id, f"👑 USERS: {cur.execute('SELECT COUNT(*) FROM users').fetchone()[0]}")
                continue

            # ================= PERSONA SWITCH =================
            if text.startswith("/persona"):
                p = text.split(" ", 1)[1] if " " in text else "normal"
                update_user(uid, persona=p)
                send(chat_id, f"🎭 Persona set to {p}", reply_to=msg_id)
                continue

            # ================= QUEUE =================
            priority = 0 if vip > time.time() else 1
            queue.put((priority, (uid, chat_id, msg_id, text)))

    except Exception as e:
        print("ERR:", e)
        time.sleep(2)
