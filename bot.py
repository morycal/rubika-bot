import requests
import time
import re

TOKEN = "1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

ADMIN_ID = 586110315

offset = 0

# ---------------- MEMORY ----------------
users = {}

# ---------------- PROVINCES ----------------
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
def start_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📱 شروع ثبت‌نام بیمه", "callback_data": "start_form"}]
        ]
    }

def province_keyboard():
    buttons = []
    row = []

    for p in PROVINCES:
        row.append({"text": p, "callback_data": f"p_{p}"})
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    return {"inline_keyboard": buttons}

# ---------------- VALIDATION ----------------
def is_10_digit(x):
    return bool(re.fullmatch(r"\d{10}", x))

def is_phone(x):
    return bool(re.fullmatch(r"09\d{9}", x))

# ---------------- SEND TO ADMIN ----------------
def send_admin_report(user_id, user):
    msg = (
        "📥 ثبت‌نام جدید بیمه\n\n"
        f"👤 نام: {user.get('name')}\n"
        f"📱 موبایل: {user.get('phone')}\n"
        f"🧾 کد ملی: {user.get('nid')}\n"
        f"🎂 تولد: {user.get('birth')}\n"
        f"🏙 استان: {user.get('province')}\n"
        f"📍 آدرس: {user.get('address')}\n"
        f"📮 کدپستی: {user.get('postal')}\n"
        f"🆔 UserID: {user_id}"
    )

    send(ADMIN_ID, msg)

# ---------------- BOT ----------------
print("🚀 INSURANCE SYSTEM STARTED")

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

                if chat_id not in users:
                    users[chat_id] = {"step": "start"}

                user = users[chat_id]

                # START
                if text == "/start":
                    user["step"] = "wait_phone"

                    send(chat_id,
                         "🏢 به سامانه بیمه خوش آمدید\n\n"
                         "برای شروع روی دکمه زیر بزنید 👇",
                         start_keyboard())

                # PHONE
                elif user["step"] == "wait_phone":
                    if not is_phone(text):
                        send(chat_id, "❌ شماره صحیح نیست (09xxxxxxxxx)")
                    else:
                        user["phone"] = text
                        user["step"] = "name"
                        send(chat_id, "👤 نام و نام خانوادگی:")

                # NAME
                elif user["step"] == "name":
                    user["name"] = text
                    user["step"] = "nid"
                    send(chat_id, "🧾 کد ملی (10 رقم):")

                # NID
                elif user["step"] == "nid":
                    if not is_10_digit(text):
                        send(chat_id, "❌ کد ملی باید 10 رقم باشد")
                    else:
                        user["nid"] = text
                        user["step"] = "birth"
                        send(chat_id, "🎂 تاریخ تولد:")

                # BIRTH
                elif user["step"] == "birth":
                    user["birth"] = text
                    user["step"] = "province"
                    send(chat_id, "🏙 استان خود را انتخاب کنید:", province_keyboard())

                # ADDRESS
                elif user["step"] == "address":
                    user["address"] = text
                    user["step"] = "postal"
                    send(chat_id, "📮 کد پستی (10 رقم):")

                # POSTAL
                elif user["step"] == "postal":
                    if not is_10_digit(text):
                        send(chat_id, "❌ کد پستی باید 10 رقم باشد")
                    else:
                        user["postal"] = text
                        user["step"] = "done"

                        send(chat_id,
                             "🎉 ثبت‌نام کامل شد")

                        # SEND TO ADMIN
                        send_admin_report(chat_id, user)

            # ---------------- CALLBACK ----------------
            if "callback_query" in update:
                cb = update["callback_query"]
                chat_id = cb["message"]["chat"]["id"]
                data = cb["data"]

                if chat_id not in users:
                    users[chat_id] = {"step": "start"}

                user = users[chat_id]

                # START FORM
                if data == "start_form":
                    user["step"] = "wait_phone"
                    send(chat_id, "📱 شماره موبایل خود را وارد کنید:")

                # PROVINCE
                elif data.startswith("p_"):
                    province = data.replace("p_", "")
                    user["province"] = province

                    user["step"] = "address"
                    send(chat_id, "📍 آدرس دقیق را وارد کنید:")

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
