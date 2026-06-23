import os
import time
import sqlite3
import requests
import threading
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
questions INTEGER DEFAULT 0,
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

# ================= BOT HELPERS =================
def send(chat_id, text, reply_to=None, reply_markup=None):
    data = {
        "chat_id": chat_id,
        "text": text[:4000],
    }
    if reply_to:
        data["reply_to_message_id"] = reply_to
    if reply_markup:
        data["reply_markup"] = reply_markup

    requests.post(f"{BASE_URL}/sendMessage", json=data)

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

# ================= AI =================
def ask_ai(text):
    res = client.chat.completions.create(
        model="Qwen/Qwen3-8B",
        messages=[
            {"role": "system", "content": "تو موری هستی، دستیار فارسی هوشمند و پاسخگو."},
            {"role": "user", "content": text}
        ],
        max_tokens=300
    )
    return res.choices[0].message.content

# ================= ADMIN PANEL =================
def admin_menu(chat_id):
    send(chat_id,
         "👑 پنل ادمین",
         reply_markup={
             "inline_keyboard": [
                 [{"text": "💎 VIP", "callback_data": "adm_vip"}],
                 [{"text": "💳 پرداخت‌ها", "callback_data": "adm_pay"}],
                 [{"text": "🚫 بن", "callback_data": "adm_ban"}],
                 [{"text": "📊 آمار", "callback_data": "adm_stats"}],
             ]
         })

# ================= VIP =================
def vip_menu(chat_id):
    send(chat_id, "💎 پلن‌ها:",
         reply_markup={
             "inline_keyboard": [
                 [{"text": "1 روز", "callback_data": "vip_1"}],
                 [{"text": "7 روز", "callback_data": "vip_7"}],
                 [{"text": "30 روز", "callback_data": "vip_30"}],
             ]
         })

# ================= CALLBACK =================
def handle_callback(cq):
    data = cq["data"]
    chat_id = cq["message"]["chat"]["id"]
    uid = cq["from"]["id"]

    if uid == ADMIN_ID and data == "/admin":
        admin_menu(chat_id)
        return

    if data.startswith("vip_"):
        plan_days = {"vip_1":1,"vip_7":7,"vip_30":30}
        set_state(uid, data)
        send(chat_id, f"💳 کارت: {CARD}\nکد پرداخت را ارسال کنید")
        return

    if data == "adm_stats":
        cur.execute("SELECT COUNT(*) FROM users")
        u = cur.fetchone()[0]
        send(chat_id, f"👥 کاربران: {u}")
        return

    if data == "adm_pay":
        cur.execute("SELECT id,user_id,tracking FROM payments WHERE status=0")
        rows = cur.fetchall()
        text = "\n".join([f"{r[0]} | {r[1]} | {r[2]}" for r in rows]) or "خالی"
        send(chat_id, text)
        return

    if data.startswith("pay_ok_"):
        pid = int(data.split("_")[2])
        cur.execute("UPDATE payments SET status=1,paid_at=? WHERE id=?", (time.time(), pid))
        db.commit()
        send(chat_id, "✅ تایید شد")
        return

    if data.startswith("pay_no_"):
        pid = int(data.split("_")[2])
        cur.execute("UPDATE payments SET status=-1 WHERE id=?", (pid,))
        db.commit()
        send(chat_id, "❌ رد شد")
        return

# ================= MAIN BOT =================
print("BOT RUNNING")

threading.Thread(target=run_api).start()

offset = 0

while True:
    try:
        data = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": offset, "timeout": 30}
        ).json()

        for upd in data.get("result", []):
            offset = upd["update_id"] + 1

            # CALLBACK
            if "callback_query" in upd:
                handle_callback(upd["callback_query"])
                continue

            if "message" not in upd:
                continue

            msg = upd["message"]
            uid = msg["from"]["id"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text","")
            msg_id = msg.get("message_id")

            vip, last, banned, state = get_user(uid)

            now = int(time.time())

            if banned:
                continue

            if text == "/admin" and uid == ADMIN_ID:
                admin_menu(chat_id)
                continue

            if text == "/start":
                send(chat_id, "👋 سلام", reply_to=msg_id)
                continue

            # PAYMENT
            if state.startswith("vip_") and text:
                cur.execute("""
                    INSERT INTO payments(user_id,plan,tracking)
                    VALUES(?,?,?)
                """, (uid, state, text))
                db.commit()

                days = {"vip_1":1,"vip_7":7,"vip_30":30}.get(state,0)
                set_vip(uid, days)

                set_state(uid, "")

                send(chat_id, "✅ VIP فعال شد", reply_to=msg_id)
                continue

            # AI MORI
            if text:
                try:
                    reply = ask_ai(text)
                    send(chat_id, reply, reply_to=msg_id)
                except:
                    send(chat_id, "خطا", reply_to=msg_id)

    except Exception as e:
        print("ERR:", e)
        time.sleep(3)
