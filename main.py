import requests
import time
import random

TOKEN = "1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

OWNER_ID = 586110315

last_update_id = 0
BOT_ENABLED = True

owner_answers = {
    "سلام": "سلام ملعون بزرگ 😈",
    "خوبی": "فدات ملعون، تو هم که همیشه خوبی 😂",
    "چطوری": "عالی‌ام ملعون 😊",
    "صبح بخیر": "صبح شما بخیر مارمولک ☀️",
    "شب بخیر": "شب شما هم بخیر ملعون اعظم 🌙",
    "مرسی": "قربان شما ❤️",
    "ممنون": "خواهش می‌کنم خوابالو ❤️",
    "چه خبر": "سلامتی ترنک 😊"
}

challenges = [
    "20 شنا برو",
    "30 درازنشست برو",
    "10 دقیقه پیاده‌روی کن",
    "به 3 نفر سلام کن",
    "یک صفحه کتاب بخوان",
    "5 دقیقه ورزش کن",
    "10 دقیقه زبان بخوان",
    "اتاقت را مرتب کن",
    "به یک دوست پیام بده",
    "یک لیوان آب بنوش",
    "5 دقیقه مدیتیشن کن",
    "امروز هیچ دروغی نگو",
    "به یک نفر کمک کن",
    "20 بار طناب مجازی بزن",
    "یک کار خوب انجام بده",
    "10 دقیقه بدون موبایل باش",
    "یک جوک تعریف کن",
    "به پدر یا مادرت کمک کن",
    "یک چیز جدید یاد بگیر",
    "20 ثانیه پلانک برو"
]

def send_message(chat_id, text, reply_to=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_to is not None:
        data["reply_to_message_id"] = reply_to

    requests.post(
        f"{BASE_URL}/sendMessage",
        json=data,
        timeout=10
    )

while True:
    try:
        response = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": last_update_id + 1},
            timeout=20
        ).json()

        for update in response.get("result", []):

            last_update_id = update["update_id"]

            if "message" not in update:
                continue

            message = update["message"]

            chat_id = message["chat"]["id"]
            user_id = message["from"]["id"]
            message_id = message["message_id"]

            text = message.get("text", "").strip()

            if not text:
                continue

            # چالش تصادفی
            if text == "چالش":
                send_message(
                    chat_id,
                    f"🎯 چالش تصادفی:\n\n{random.choice(challenges)}",
                    reply_to=message_id
                )
                continue

            # دستورات ادمین
            if user_id == OWNER_ID:

                if text == "خاموش":
                    BOT_ENABLED = False
                    send_message(
                        chat_id,
                        "🔴 ربات خاموش شد",
                        reply_to=message_id
                    )
                    continue

                elif text == "روشن":
                    BOT_ENABLED = True
                    send_message(
                        chat_id,
                        "🟢 ربات روشن شد",
                        reply_to=message_id
                    )
                    continue

            # اگر خاموش باشد فقط ادمین اجازه استفاده دارد
            if not BOT_ENABLED and user_id != OWNER_ID:
                continue

            # پاسخ‌های ادمین
            if user_id == OWNER_ID:

                reply = owner_answers.get(
                    text,
                    "چی چی میگویی ملعون؟ 😈"
                )

            # پاسخ کاربران عادی
            else:

                if text == "/start":
                    reply = "سلام 👋\nبه ربات خوش آمدید"

                elif text == "سلام":
                    reply = "سلام 👋"

                elif text == "خوبی":
                    reply = "ممنون، خوبم 😊"

                elif text == "شب بخیر":
                    reply = "شب شما هم بخیر 🌙"

                elif text == "صبح بخیر":
                    reply = "صبح شما هم بخیر ☀️"

                else:
                    reply = "هااان؟؟ 🤔"

            send_message(
                chat_id,
                reply,
                reply_to=message_id
            )

        time.sleep(1)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)
