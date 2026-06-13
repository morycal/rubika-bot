import requests
import time
import sqlite3
import re

TOKEN = "1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

ADMIN_ID = 586110315

offset = 0

# ---------------- DATABASE ----------------
conn = sqlite3.connect("insurance.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    chat_id INTEGER PRIMARY KEY,
    phone TEXT,
    name TEXT,
    nid TEXT,
    birth TEXT,
    province TEXT,
    address TEXT,
    postal TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    status TEXT,
    date TEXT
)
""")

conn.commit()

# ---------------- MEMORY ----------------
steps = {}

# ---------------- SEND ----------------
def send(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(f"{BASE_URL}/sendMessage", json=payload)

# ---------------- KEYBOARDS ----------------
def main_menu():
    return {
        "inline_keyboard": [
            [{"text": "🛒 سفارش بیمه", "callback_data": "new_order"}],
            [{"text": "📦 سبد خرید", "callback_data": "cart"}],
            [{"text": "📑 پیگیری سفارش", "callback_data": "track"}],
            [{"text": "👤 پروفایل", "callback_data": "profile"}]
        ]
    }

def start_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🚀 شروع / ورود", "callback_data": "start"}]
        ]
    }

# ---------------- CHECK USER ----------------
def get_user(chat_id):
    cur.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,))
    return cur.fetchone()

# ---------------- SAVE USER ----------------
def save_user(chat_id, data):
    cur.execute("""
    INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?,?,?)
    """, (
        chat_id,
        data.get("phone"),
        data.get("name"),
        data.get("nid"),
        data.get("birth"),
        data.get("province"),
        data.get("address"),
        data.get("postal")
    ))
    conn.commit()

# ---------------- VALIDATION ----------------
def is_phone(x): return bool(re.fullmatch(r"09\d{9}", x))
def is_10(x): return bool(re.fullmatch(r"\d{10}", x))

# ---------------- MENU ----------------
def show_menu(chat_id):
    send(chat_id,
         "🏢 پنل بیمه شما 👇",
         main_menu())

# ---------------- BOT ----------------
print("🚀 INSURANCE CRM STARTED")

while True:
    try:
        res = requests.post(
            f"{BASE_URL}/getUpdates",
            json={"offset": offset},
            timeout=20
        )

        updates = res.json().get("result", [])

        for update in updates:
            offset = update["update_id"] + 1

            # ---------------- MESSAGE ----------------
            if "message" in update:
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "").strip()

                user = get_user(chat_id)

                # ---------------- START ----------------
                if text == "/start":

                    if user:
                        show_menu(chat_id)
                    else:
                        steps[chat_id] = {"step": "phone"}

                        send(chat_id,
                             "🏢 خوش آمدید به بیمه هوشمند\n\n"
                             "📱 شماره موبایل خود را وارد کنید:")

                # ---------------- REGISTRATION FLOW ----------------
                elif chat_id in steps:

                    step = steps[chat_id]["step"]

                    # PHONE
                    if step == "phone":
                        if not is_phone(text):
                            send(chat_id, "❌ شماره اشتباه است")
                        else:
                            steps[chat_id]["phone"] = text
                            steps[chat_id]["step"] = "name"
                            send(chat_id, "👤 نام و نام خانوادگی:")

                    # NAME
                    elif step == "name":
                        steps[chat_id]["name"] = text
                        steps[chat_id]["step"] = "nid"
                        send(chat_id, "🧾 کد ملی (10 رقم):")

                    # NID
                    elif step == "nid":
                        if not is_10(text):
                            send(chat_id, "❌ کد ملی باید 10 رقم باشد")
                        else:
                            steps[chat_id]["nid"] = text
                            steps[chat_id]["step"] = "birth"
                            send(chat_id, "🎂 تاریخ تولد:")

                    # BIRTH
                    elif step == "birth":
                        steps[chat_id]["birth"] = text
                        steps[chat_id]["step"] = "province"
                        send(chat_id, "🏙 استان خود را وارد کنید:")

                    # PROVINCE
                    elif step == "province":
                        steps[chat_id]["province"] = text
                        steps[chat_id]["step"] = "address"
                        send(chat_id, "📍 آدرس کامل:")

                    # ADDRESS
                    elif step == "address":
                        steps[chat_id]["address"] = text
                        steps[chat_id]["step"] = "postal"
                        send(chat_id, "📮 کد پستی (10 رقم):")

                    # POSTAL
                    elif step == "postal":
                        if not is_10(text):
                            send(chat_id, "❌ کد پستی اشتباه است")
                        else:
                            steps[chat_id]["postal"] = text

                            save_user(chat_id, steps[chat_id])
                            steps.pop(chat_id)

                            send(chat_id,
                                 "🎉 ثبت‌نام کامل شد")

                            show_menu(chat_id)

            # ---------------- CALLBACK ----------------
            if "callback_query" in update:
                cb = update["callback_query"]
                chat_id = cb["message"]["chat"]["id"]
                data = cb["data"]

                user = get_user(chat_id)

                # ---------------- START ----------------
                if data == "start":
                    if user:
                        show_menu(chat_id)
                    else:
                        steps[chat_id] = {"step": "phone"}
                        send(chat_id, "📱 شماره موبایل:")

                # ---------------- MENU ----------------
                elif data == "new_order":
                    send(chat_id, "🛒 اینجا سفارش بیمه بزودی فعال می‌شود")

                elif data == "cart":
                    send(chat_id, "📦 سبد خرید شما خالی است")

                elif data == "track":
                    send(chat_id, "📑 هیچ سفارشی ثبت نشده")

                elif data == "profile":
                    if user:
                        send(chat_id,
                             f"👤 پروفایل:\n"
                             f"📱 {user[1]}\n"
                             f"🧾 {user[2]}\n"
                             f"🏙 {user[5]}\n"
                             f"📍 {user[6]}")
                    else:
                        send(chat_id, "❌ ابتدا ثبت‌نام کنید")

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
