import os
import time
import sqlite3
import requests
from openai import OpenAI

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
status INTEGER DEFAULT 0
)
""")

db.commit()

# ================= SEND =================
def send(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text[:4000]}
    if reply_markup:
        data["reply_markup"] = reply_markup

    requests.post(f"{BASE_URL}/sendMessage", json=data)

# ================= USER =================
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

# ================= UI =================
def start_menu(chat_id):
    send(chat_id,
         "👋 خوش آمدید",
         reply_markup={
             "inline_keyboard": [
                 [{"text": "👤 پروفایل", "callback_data": "profile"}],
                 [{"text": "💎 خرید VIP", "callback_data": "buy_vip"}],
                 [{"text": "🤖 چت با AI", "callback_data": "ai"}],
                 [{"text": "🧑‍💻 پشتیبانی", "url": "https://t.me/ahmmad24"}]
             ]
         })

def vip_menu(chat_id):
    send(chat_id, "💎 انتخاب پلن:",
         reply_markup={
             "inline_keyboard": [
                 [{"text": "📅 روزانه - 10k", "callback_data": "vip_1"}],
                 [{"text": "📆 هفتگی - 50k", "callback_data": "vip_7"}],
                 [{"text": "🗓 ماهانه - 150k", "callback_data": "vip_30"}],
                 [{"text": "💎 سالانه - 1M", "callback_data": "vip_365"}],
             ]
         })

# ================= AI =================
def ask_ai(text):
    res = client.chat.completions.create(
        model="Qwen/Qwen3-8B",
        messages=[
            {"role": "system", "content": "تو یک دستیار فارسی حرفه‌ای هستی"},
            {"role": "user", "content": text}
        ],
        max_tokens=300
    )
    return res.choices[0].message.content

# ================= MAIN =================
print("BOT STARTED")

offset = 0

while True:
    try:
        data = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": offset, "timeout": 30}
        ).json()

        for upd in data.get("result", []):

            offset = upd["update_id"] + 1

            # ================= CALLBACK =================
            if "callback_query" in upd:
                cq = upd["callback_query"]
                data_cb = cq["data"]
                chat_id = cq["message"]["chat"]["id"]
                uid = cq["from"]["id"]

                # -------- START MENU ACTIONS --------
                if data_cb == "buy_vip":
                    vip_menu(chat_id)
                    continue

                if data_cb == "profile":
                    q, vip, last, state = get_user(uid)
                    send(chat_id,
                         f"👤 پروفایل\n"
                         f"📊 سوالات: {q}\n"
                         f"💎 VIP: {'فعال' if vip > time.time() else 'غیرفعال'}")
                    continue

                if data_cb == "ai":
                    set_state(uid, "ai")
                    send(chat_id, "🤖 حالا پیام بده...")
                    continue

                # -------- VIP SELECT --------
                plans = {
                    "vip_1": (1, 10000),
                    "vip_7": (7, 50000),
                    "vip_30": (30, 150000),
                    "vip_365": (365, 1000000)
                }

                if data_cb in plans:
                    days, price = plans[data_cb]

                    set_state(uid, f"pay_{days}")

                    send(chat_id,
                         f"💳 پلن انتخاب شد\n"
                         f"💰 قیمت: {price}\n"
                         f"💳 کارت:\n{CARD}\n\n"
                         f"👇 حالا کد پرداخت را ارسال کنید",
                         reply_markup={
                             "inline_keyboard": [
                                 [{"text": "📩 ارسال کد پرداخت", "callback_data": "send_code"}]
                             ]
                         })
                    continue

                if data_cb == "send_code":
                    send(chat_id, "✍️ کد پرداخت را همینجا ارسال کنید")
                    continue

                continue

            # ================= MESSAGE =================
            if "message" not in upd:
                continue

            msg = upd["message"]
            uid = msg["from"]["id"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "").strip()

            if not text:
                continue

            q, vip, last, state = get_user(uid)

            now = int(time.time())

            if uid != ADMIN_ID and now - last < 3:
                send(chat_id, "⏳ صبر کن")
                continue

            update_last(uid, now)

            # ================= /start =================
            if text == "/start":
                start_menu(chat_id)
                continue

            # ================= VIP LIMIT =================
            if vip < now and q >= 5:
                send(chat_id,
                     "🚫 محدود شدی",
                     reply_markup={
                         "inline_keyboard": [
                             [{"text": "💎 خرید VIP", "callback_data": "buy_vip"}]
                         ]
                     })
                continue

            # ================= PAYMENT INPUT =================
            if state.startswith("pay_"):

                plan_days = state.split("_")[1]

                cur.execute("""
                    INSERT INTO payments(user_id,plan,tracking)
                    VALUES(?,?,?)
                """, (uid, plan_days, text))
                db.commit()

                set_state(uid, "")

                send(chat_id, "✅ ثبت شد، منتظر تایید ادمین باشید")
                send(ADMIN_ID, f"💳 پرداخت جدید\nUser:{uid}\nPlan:{plan_days}\nCode:{text}")
                continue

            # ================= AI =================
            try:
                answer = ask_ai(text)
                send(chat_id, answer)
            except:
                send(chat_id, "❌ خطا")

    except Exception as e:
        print("ERR:", e)
        time.sleep(3)
