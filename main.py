# main.py
# Corrected basic version based on the code provided by user

import os
import time
import sqlite3
import requests
from openai import OpenAI

BALE_TOKEN = os.getenv("BALE_TOKEN", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "586110315"))

CARD_NUMBER = "1010202030304040"
SUPPORT = "@ahmmad24"

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

BASE_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
questions INTEGER DEFAULT 0,
vip_until INTEGER DEFAULT 0,
banned INTEGER DEFAULT 0,
last_message INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS history(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
role TEXT,
message TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS payments(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
plan TEXT,
tracking_code TEXT,
status INTEGER DEFAULT 0,
created_at INTEGER
)
""")

db.commit()

def send(chat_id, text):
    requests.post(
        f"{BASE_URL}/sendMessage",
        json={"chat_id": chat_id, "text": str(text)[:4000]},
        timeout=30
    )

def get_user(uid):
    cur.execute(
        "SELECT questions,vip_until,banned,last_message FROM users WHERE user_id=?",
        (uid,)
    )
    row = cur.fetchone()

    if row:
        return row

    cur.execute("INSERT INTO users(user_id) VALUES(?)", (uid,))
    db.commit()
    return (0, 0, 0, 0)

def add_history(uid, role, msg):
    cur.execute(
        "INSERT INTO history(user_id,role,message) VALUES(?,?,?)",
        (uid, role, msg[:3000])
    )
    db.commit()

def ask_ai(uid, text):
    msgs = [{"role": "system", "content": "تو یک دستیار فارسی حرفه‌ای هستی."}]

    cur.execute("""
    SELECT role,message
    FROM history
    WHERE user_id=?
    ORDER BY id DESC
    LIMIT 10
    """, (uid,))

    rows = cur.fetchall()[::-1]

    for r, m in rows:
        msgs.append({"role": r, "content": m})

    msgs.append({"role": "user", "content": text})

    res = client.chat.completions.create(
        model="Qwen/Qwen3-8B",
        messages=msgs,
        max_tokens=300
    )

    return res.choices[0].message.content

print("BOT STARTED")
offset = 0

while True:
    try:
        data = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": offset, "timeout": 30},
            timeout=35
        ).json()

        for upd in data.get("result", []):

            print(upd)

            offset = upd["update_id"] + 1

            if "message" not in upd:
                continue

            msg = upd["message"]
            uid = msg["from"]["id"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "").strip()

            if not text:
                continue

            q, vip, banned, last = get_user(uid)

            if banned:
                send(chat_id, "⛔ شما مسدود هستید.")
                continue

            now = int(time.time())

            if uid != ADMIN_ID and now - last < 5:
                send(chat_id, "⏳ کمی صبر کنید.")
                continue

            cur.execute(
                "UPDATE users SET last_message=? WHERE user_id=?",
                (now, uid)
            )
            db.commit()

            if text == "/start":
                send(chat_id, "🤖 ربات فعال است.")
                continue

            try:
                answer = ask_ai(uid, text)

                add_history(uid, "user", text)
                add_history(uid, "assistant", answer)

                send(chat_id, answer)

            except Exception as e:
                send(chat_id, f"خطا: {e}")

    except Exception as e:
        print("ERR", e)
        time.sleep(5)
