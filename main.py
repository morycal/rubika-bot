import os
import time
import sqlite3
import requests
import threading
import re
from flask import Flask, jsonify
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
db = sqlite3.connect("mori_ultra.db", check_same_thread=False)
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
amount INTEGER,
status TEXT DEFAULT 'pending',
ts INTEGER
)
""")

db.commit()

# ================= SEND =================
def send(chat_id, text, reply_to=None, reply_markup=None):
    data = {"chat_id": chat_id, "text": text[:4000]}
    if reply_to:
        data["reply_to_message_id"] = reply_to
    if reply_markup:
        data["reply_markup"] = reply_markup
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

def update(uid, **kwargs):
    for k, v in kwargs.items():
        cur.execute(f"UPDATE users SET {k}=? WHERE user_id=?", (v, uid))
    db.commit()

# ================= DAILY LIMIT =================
def reset_daily(uid):
    today = int(time.time() // 86400)
    cur.execute("SELECT last_reset FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()[0]

    if r != today:
        cur.execute("""
            UPDATE users
            SET daily_count=0,last_reset=?
            WHERE user_id=?
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

# ================= MEMORY =================
def save_memory(uid, role, text):
    cur.execute("""
        INSERT INTO memory(user_id,role,content,ts)
        VALUES(?,?,?,?)
    """, (uid, role, text, int(time.time())))
    db.commit()

def load_memory(uid):
    cur.execute("""
        SELECT role,content FROM memory
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 8
    """, (uid,))
    rows = cur.fetchall()
    return [{"role": r, "content": c} for r, c in reversed(rows)]

# ================= MORI DETECTOR =================
def is_calling_mori(msg, text):
    if msg["chat"]["type"] == "private":
        return True

    if msg.get("reply_to_message"):
        return True

    if re.search(r"\b(موری|mori|@mori)\b", text.lower()):
        return True

    for e in msg.get("entities", []):
        if e.get("type") == "mention":
            return True

    return False

# ================= AI =================
def ask_ai(uid, text):
    messages = [
        {"role": "system", "content": "تو موری هستی، دستیار هوشمند فارسی. کوتاه، دقیق و کاربردی جواب بده."}
    ]

    messages += load_memory(uid)
    messages.append({"role": "user", "content": text})

    res = client.chat.completions.create(
        model="Qwen/Qwen3-8B",
        messages=messages,
        max_tokens=300
    )

    return res.choices[0].message.content

# ================= BUTTON MENUS =================
def shop(chat_id):
    send(chat_id,
         "💎 خرید اشتراک",
         reply_markup={
             "inline_keyboard": [
                 [{"text": "🥉 7 روز VIP", "callback_data": "vip_7"}],
                 [{"text": "🥈 30 روز VIP", "callback_data": "vip_30"}],
                 [{"text": "🥇 365 روز VIP", "callback_data": "vip_365"}],
             ]
         })

def admin_panel(chat_id):
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    send(chat_id,
         f"""👑 ADMIN PANEL

👥 Users: {users}
📊 Daily system active
""")

# ================= CALLBACK =================
def handle_callback(data, chat_id, uid):
    if data == "shop":
        shop(chat_id)

    if data.startswith("vip_"):
        days = {"vip_7":7,"vip_30":30,"vip_365":365}[data]

        cur.execute("""
            INSERT INTO payments(user_id,plan,amount,ts)
            VALUES(?,?,?,?)
        """, (uid, data, days*1000, int(time.time())))
        db.commit()

        update(uid, vip_until=int(time.time()) + days*86400)

        send(chat_id, "✅ اشتراک فعال شد")

# ================= MAIN =================
offset = 0

print("MORI ULTRA RUNNING")

while True:
    try:
        res = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": offset, "timeout": 30}
        ).json()

        for upd in res.get("result", []):
            offset = upd["update_id"] + 1

            # ===== CALLBACK =====
            if "callback_query" in upd:
                cq = upd["callback_query"]
                handle_callback(
                    cq["data"],
                    cq["message"]["chat"]["id"],
                    cq["from"]["id"]
                )
                continue

            if "message" not in upd:
                continue

            msg = upd["message"]
            uid = msg["from"]["id"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")
            msg_id = msg.get("message_id")

            vip_until, daily, last_reset, banned = get_user(uid)

            if banned:
                continue

            if text == "/shop":
                shop(chat_id)
                continue

            if uid == ADMIN_ID and text == "/admin":
                admin_panel(chat_id)
                continue

            # ===== LIMIT =====
            if not can_use(uid, vip_until):
                send(chat_id, "⛔ محدودیت 10 پیام روزانه تمام شد", reply_to=msg_id)
                continue

            # ===== GROUP FILTER =====
            if msg["chat"]["type"] != "private":
                if not is_calling_mori(msg, text):
                    continue

            inc(uid)

            reply = ask_ai(uid, text)

            send(chat_id, reply, reply_to=msg_id)

            save_memory(uid, "user", text)
            save_memory(uid, "assistant", reply)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)
