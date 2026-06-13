import requests
import time

TOKEN = "1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0

# ---------------- TEMP DATABASE ----------------
users = {}

# ---------------- SEND ----------------
def send(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    requests.post(f"{BASE_URL}/sendMessage", json=payload)


# ---------------- KEYBOARDS ----------------

def start_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📱 تایید شماره موبایل", "callback_data": "phone"}]
        ]
    }


def city_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "تهران", "callback_data": "city_tehran"},
                {"text": "مشهد", "callback_data": "city_mashhad"}
            ],
            [
                {"text": "اصفهان", "callback_data": "city_isfahan"},
                {"text": "شیراز", "callback_data": "city_shiraz"}
            ]
        ]
    }


# ---------------- MAIN ----------------

print("🚀 INSURANCE BOT STARTED")

while True:
    try:
        res = requests.post(
            f"{BASE_URL}/getUpdates",
            json={"offset": offset},
            timeout=15
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
                        "🏢 به سامانه ثبت‌نام بیمه خوش آمدید 👋\n\n"
                        "برای ادامه روی دکمه زیر کلیک کنید:",
                        start_keyboard()
                    )

                # PHONE STEP
                elif user["step"] == "wait_phone":
                    user["phone"] = text
                    user["step"] = "name"

                    send(chat_id, "👤 نام و نام خانوادگی خود را وارد کنید:")

                # NAME STEP
                elif user["step"] == "name":
                    user["name"] = text
                    user["step"] = "national_id"

                    send(chat_id, "🆔 کد ملی را وارد کنید:")

                # NATIONAL ID
                elif user["step"] == "national_id":
                    user["nid"] = text
                    user["step"] = "birth"

                    send(chat_id, "🎂 تاریخ تولد (مثلاً 1380/01/01):")

                # BIRTH
                elif user["step"] == "birth":
                    user["birth"] = text
                    user["step"] = "city"

                    send(chat_id,
                         "🏙 استان خود را انتخاب کنید:",
                         city_keyboard())

                # ADDRESS STEP
                elif user["step"] == "address":
                    user["address"] = text
                    user["step"] = "postal"

                    send(chat_id, "📮 کد پستی را وارد کنید:")

                # POSTAL
                elif user["step"] == "postal":
                    user["postal"] = text
                    user["step"] = "done"

                    send(chat_id,
                         "✅ ثبت‌نام تکمیل شد 🎉\n\n"
                         f"👤 {user['name']}\n"
                         f"📱 {user['phone']}\n"
                         f"🆔 {user['nid']}\n"
                         f"🎂 {user['birth']}\n"
                         f"🏙 {user.get('city','')}\n"
                         f"📮 {user['postal']}\n"
                         f"📍 {user.get('address','')}\n")

            # ---------------- CALLBACK ----------------
            if "callback_query" in update:
                cb = update["callback_query"]
                chat_id = cb["message"]["chat"]["id"]
                data_cb = cb["data"]

                if chat_id not in users:
                    users[chat_id] = {"step": "start"}

                user = users[chat_id]

                # PHONE BUTTON
                if data_cb == "phone":
                    user["step"] = "wait_phone"

                    send(chat_id,
                         "📱 لطفاً شماره موبایل خود را وارد کنید:")

                # CITY SELECTION
                elif data_cb.startswith("city_"):
                    city = data_cb.split("_")[1]

                    user["city"] = city
                    user["step"] = "address"

                    send(chat_id,
                         "📍 آدرس دقیق خود را وارد کنید:")

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
