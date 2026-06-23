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
state TEXT DEFAULT ''
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

# ================= FLASK API =================
app = Flask(__name__)

@app.route("/api/revenue")
def revenue():
    cur.execute("""
        SELECT paid_at, amount
        FROM payments
        WHERE status=1
    """)

    rows = cur.fetchall()

    data = {}

    for t, a in rows:
        if not t:
            continue
        day = time.strftime("%Y-%m-%d", time.localtime(t))
        data[day] = data.get(day, 0) + a

    return jsonify([
        {"date": k, "amount": v}
        for k, v in sorted(data.items())
    ])

def run_api():
    app.run(host="0.0.0.0", port=5000)

# ================= BOT =================
def send(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text[:4000]}
    if reply_markup:
        data["reply_markup"] = reply_markup
    requests.post(f"{BASE_URL}/sendMessage", json=data)

def get_user(uid):
    cur.execute("SELECT questions,vip_until,last_message,state FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO users(user_id) VALUES(?)", (uid,))
        db.commit()
        return (0, 0, 0, "")
    return row

def set_state(uid, state):
    cur.execute("UPDATE users SET state=? WHERE user_id=?", (state, uid))
    db.commit()

def update_last(uid, now):
    cur.execute("UPDATE users SET last_message=? WHERE user_id=?", (now, uid))
    db.commit()

# ================= VIP =================
PLANS = {
    "vip_1": (1, 10000),
    "vip_7": (7, 50000),
    "vip_30": (30, 150000),
    "vip_365": (365, 1000000)
}

def activate_vip(uid, plan):
    days, price = PLANS.get(plan, (0, 0))
    now = int(time.time())

    cur.execute("SELECT vip_until FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    old = row[0] if row else 0

    new_vip = max(now, old) + days * 86400

    cur.execute("UPDATE users SET vip_until=? WHERE user_id=?", (new_vip, uid))
    db.commit()

# ================= AI =================
def ask_ai(text):
    res = client.chat.completions.create(
        model="Qwen/Qwen3-8B",
        messages=[
            {"role": "system", "content": "تو یک دستیار فارسی حرفه‌ای هستی."},
            {"role": "user", "content": text}
        ],
        max_tokens=300
    )
    return res.choices[0].message.content

# ================= UI =================
def start_menu(chat_id):
    send(chat_id,
         "👋 خوش آمدید",
         reply_markup={
             "inline_keyboard": [
                 [{"text": "👤 پروفایل", "callback_data": "profile"}],
                 [{"text": "💎 خرید VIP", "callback_data": "vip_menu"}],
                 [{"text": "📊 داشبورد درآمد", "callback_data": "dashboard"}]
             ]
         })

def vip_menu(chat_id):
    send(chat_id, "💎 انتخاب پلن:",
         reply_markup={
             "inline_keyboard": [
                 [{"text": "روزانه", "callback_data": "vip_1"}],
                 [{"text": "هفتگی", "callback_data": "vip_7"}],
                 [{"text": "ماهانه", "callback_data": "vip_30"}],
                 [{"text": "سالانه", "callback_data": "vip_365"}],
             ]
         })

def dashboard(chat_id):
    cur.execute("SELECT SUM(amount) FROM payments WHERE status=1")
    total = cur.fetchone()[0] or 0

    cur.execute("SELECT SUM(amount) FROM payments WHERE status=1 AND paid_at>?", (time.time()-86400,))
    today = cur.fetchone()[0] or 0

    send(chat_id,
         f"""
📊 داشبورد درآمد

💰 کل: {total}
📅 امروز: {today}
""")

# ================= MAIN =================
print("BOT STARTED + API RUNNING")

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

            # ========== CALLBACK ==========
            if "callback_query" in upd:
                cq = upd["callback_query"]
                d = cq["data"]
                chat_id = cq["message"]["chat"]["id"]
                uid = cq["from"]["id"]

                if d == "vip_menu":
                    vip_menu(chat_id)
                    continue

                if d == "dashboard":
                    dashboard(chat_id)
                    continue

                if d in PLANS:
                    set_state(uid, d)
                    send(chat_id, f"💳 کارت: {CARD}\n📩 کد پرداخت را ارسال کنید")
                    continue

                if d == "profile":
                    q,vip,last,st = get_user(uid)
                    send(chat_id, f"👤 VIP: {'فعال' if vip>time.time() else 'غیرفعال'}")
                    continue

                continue

            # ========== MESSAGE ==========
            if "message" not in upd:
                continue

            msg = upd["message"]
            uid = msg["from"]["id"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text","").strip()

            if not text:
                continue

            q,vip,last,state = get_user(uid)

            now = int(time.time())

            if uid != ADMIN_ID and now-last < 3:
                send(chat_id, "⏳ صبر کن")
                continue

            update_last(uid, now)

            if text == "/start":
                start_menu(chat_id)
                continue

            if state in PLANS:
                cur.execute("""
                    INSERT INTO payments(user_id,plan,tracking)
                    VALUES(?,?,?)
                """, (uid, state, text))
                db.commit()

                activate_vip(uid, state)

                set_state(uid, "")

                send(chat_id, "✅ پرداخت ثبت شد و VIP فعال شد")
                send(ADMIN_ID, f"💳 پرداخت\n{uid}\n{state}\n{text}")
                continue

            try:
                send(chat_id, ask_ai(text))
            except:
                send(chat_id, "خطا")

    except Exception as e:
        print("ERR:", e)
        time.sleep(3)
