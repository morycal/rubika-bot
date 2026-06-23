import os
import time
import sqlite3
import requests
import threading
import re
from flask import Flask, request, jsonify
from openai import OpenAI

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
db = sqlite3.connect("mori_world.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
vip_until INTEGER DEFAULT 0,
daily_count INTEGER DEFAULT 0,
last_reset INTEGER DEFAULT 0,
banned INTEGER DEFAULT 0,
created_at INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS logs(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
text TEXT,
response TEXT,
ts INTEGER
)
""")

db.commit()

# ================= FLASK API =================
app = Flask(__name__)

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.json
    uid = data["user_id"]
    text = data["text"]

    if not can_use(uid, get_vip(uid)):
        return jsonify({"error": "limit reached"})

    reply = ask_ai(uid, text)
    inc(uid)

    return jsonify({"response": reply})

def run_api():
    app.run(host="0.0.0.0", port=5000)

threading.Thread(target=run_api, daemon=True).start()

# ================= SEND =================
def send(chat_id, text, reply_to=None):
    data = {"chat_id": chat_id, "text": text[:4000]}
    if reply_to:
        data["reply_to_message_id"] = reply_to
    requests.post(f"{BASE_URL}/sendMessage", json=data)

# ================= USER =================
def get_user(uid):
    cur.execute("SELECT vip_until,daily_count,last_reset,banned FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()

    if not row:
        cur.execute("INSERT INTO users(user_id,created_at) VALUES(?,?)", (uid, int(time.time())))
        db.commit()
        return (0, 0, 0, 0)

    return row

def get_vip(uid):
    return get_user(uid)[0]

def update(uid, field, value):
    cur.execute(f"UPDATE users SET {field}=? WHERE user_id=?", (value, uid))
    db.commit()

# ================= LIMIT SYSTEM =================
def reset_daily(uid):
    today = int(time.time() // 86400)

    cur.execute("SELECT last_reset FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()[0]

    if r != today:
        cur.execute("""
            UPDATE users SET daily_count=0,last_reset=? WHERE user_id=?
        """, (today, uid))
        db.commit()

def can_use(uid, vip_until):
    if vip_until > time.time():
        return True

    reset_daily(uid)

    cur.execute("SELECT daily_count FROM users WHERE user_id=?", (uid,))
    count = cur.fetchone()[0]

    return count < 10

def inc(uid):
    cur.execute("UPDATE users SET daily_count=daily_count+1 WHERE user_id=?", (uid,))
    db.commit()

# ================= AI ROUTER =================
def route_model(text):
    if len(text) < 50:
        return "Qwen/Qwen3-8B"
    if "code" in text.lower():
        return "gpt-4o-mini"
    return "Qwen/Qwen3-8B"

def ask_ai(uid, text):
    model = route_model(text)

    res = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "تو MORI WORLD هستی، یک AI جهانی سریع و دقیق."},
            {"role": "user", "content": text}
        ],
        max_tokens=400
    )

    reply = res.choices[0].message.content

    cur.execute("""
        INSERT INTO logs(user_id,text,response,ts)
        VALUES(?,?,?,?)
    """, (uid, text, reply, int(time.time())))
    db.commit()

    return reply

# ================= GROUP FILTER =================
def allowed(msg, text):
    if msg["chat"]["type"] == "private":
        return True

    if msg.get("reply_to_message"):
        return True

    return bool(re.search(r"\b(موری|mori|@mori)\b", text.lower()))

# ================= BOT LOOP =================
offset = 0

print("🌍 MORI WORLD ONLINE")

while True:
    try:
        updates = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": offset, "timeout": 30}
        ).json()

        for upd in updates.get("result", []):
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

            vip = get_vip(uid)

            if not can_use(uid, vip):
                send(chat_id, "⛔ Limit 10 messages/day reached", reply_to=msg_id)
                continue

            if not allowed(msg, text):
                continue

            inc(uid)

            reply = ask_ai(uid, text)

            send(chat_id, reply, reply_to=msg_id)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)
