import requests
import time
import re

TOKEN = "1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0

# ---------------- MEMORY ----------------
users = {}

# ---------------- IRAN PROVINCES ----------------
PROVINCES = [
    "تهران", "اصفهان", "فارس", "خراسان رضوی", "خراسان شمالی", "خراسان جنوبی",
    "آذربایجان شرقی", "آذربایجان غربی", "اردبیل", "البرز", "ایلام", "بوشهر",
    "چهارمحال و بختیاری", "خوزستان", "زنجان", "سمنان", "سیستان و بلوچستان",
    "قزوین", "قم", "کردستان", "کرمان", "کرمانشاه", "کهگیلویه و بویراحمد",
    "گلستان", "گیلان", "لرستان", "مازندران", "مرکزی", "هرمزگان", "همدان", "یزد"
]

# ---------------- SEND ----------------
def send(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(f"{BASE_URL}/sendMessage", json=payload)

# ---------------- KEYBOARDS ----------------
def province_keyboard():
    buttons = []
    row = []

    for i, p in enumerate(PROVINCES):
        row.append({"text": p, "callback_data": f"p_{p}"})

        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    return {"inline_keyboard": buttons}


def start_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📱 شروع ثبت‌نام بیمه", "callback_data": "start_form"}]
        ]
    }

# ---------------- VALIDATION ----------------
def is_10_digit(value):
    return bool(re.fullmatch(r"\d{10}", value))

def is_phone_valid(text):
    return bool(re.fullmatch(r"09\d{9}", text))

# ---------------- BOT ----------------
print("🚀 INSURANCE PRO BOT STARTED")

while True:
    try:
        res = requests.post(
            f"{BASE_URL}/getUpdates",
            json={"offset": offset},
            timeout=20
        )

        data = res.json()
        updates = data.get("result", [])

        for update in updates:
            offset = update["update_id"] + 1

            # ---------------- MESSAGE ----------------
            if "message" in update:
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "").strip()

                if chat_id not in users:
                    users[chat_id] = {"step": "start"}

                user = users[chat_id]

                # START
                if text == "/start":
                    user["step"] = "phone"

                    send(
                        chat_id,
                        "🏢 خوش آمدید به سامانه بیمه\n\n"
                        "برای شروع ثبت‌نام روی دکمه زیر بزنید 👇",
                        start_keyboard()
                    )

                # PHONE INPUT (must be same user account)
                elif user["step"] == "wait_phone":
                    if not is_phone_valid(text):
                        send(chat_id, "❌ شماره معتبر نیست (مثال: 09123456789)")
                    else:
                        user["phone"] = text
                        user["step"] = "name"
                        send(chat_id, "👤 نام و نام خانوادگی را وارد کنید:")

                # NAME
                elif user["step"] == "name":
                    user["name"] = text
                    user["step"] = "nid"
                    send(chat_id, "🧾 کد ملی (10 رقم):")

                # NATIONAL ID
                elif user["step"] == "nid":
                    if not is_10_digit(text):
                        send(chat_id, "❌ کد ملی باید دقیقاً 10 رقم باشد")
                    else:
                        user["nid"] = text
                        user["step"] = "birth"
                        send(chat_id, "🎂 تاریخ تولد (مثلاً 1380/01/01):")

                # BIRTH
                elif user["step"] == "birth":
                    user["birth"] = text
                    user["step"] = "province"

                    send(chat_id,
                         "🏙 استان خود را انتخاب کنید:",
                         province_keyboard())

                # ADDRESS
                elif user["step"] == "address":
                    user["address"] = text
                    user["step"] = "postal"

                    send(chat_id, "📮 کد پستی (10 رقم):")

                # POSTAL CODE
                elif user["step"] == "postal":
                    if not is_10_digit(text):
                        send(chat_id, "❌ کد پستی باید 10 رقم باشد")
                    else:
                        user["postal"] = text
                        user["step"] = "done"

                        send(chat_id,
                             "🎉 ثبت‌نام بیمه تکمیل شد\n\n"
                             f"👤 {user['name']}\n"
                             f"📱 {user['phone']}\n"
                             f"🧾 {user['nid']}\n"
                             f"🎂 {user['birth']}\n"
                             f"🏙 {user['province']}\n"
                             f"📍 {user['address']}\n"
                             f"📮 {user['postal']}")

            # ---------------- CALLBACK ----------------
            if "callback_query" in update:
                cb = update["callback_query"]
                chat_id = cb["message"]["chat"]["id"]
                data_cb = cb["data"]

                if chat_id not in users:
                    users[chat_id] = {"step": "start"}

                user = users[chat_id]

                # START FORM
                if data_cb == "start_form":
                    user["step"] = "wait_phone"
                    send(chat_id, "📱 شماره موبایل خود را وارد کنید (09xxxxxxxxx):")

                # PROVINCE SELECT
                elif data_cb.startswith("p_"):
                    province = data_cb.replace("p_", "")

                    user["province"] = province
                    user["step"] = "address"

                    send(chat_id, "📍 آدرس دقیق خود را وارد کنید:")

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
