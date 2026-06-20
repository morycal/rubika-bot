import requests
import time
import random
from difflib import get_close_matches

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
    "یک صفحه کتاب بخوان",
    "به یک دوست پیام بده",
    "اتاقت را مرتب کن",
    "10 دقیقه زبان بخوان",
    "به یک نفر کمک کن",
    "5 دقیقه مدیتیشن کن",
    "امروز هیچ دروغی نگو"
]

truths = [
    "بزرگ‌ترین ترست چیه؟",
    "آخرین باری که گریه کردی کی بود؟",
    "بامزه‌ترین خاطره‌ات چیه؟",
    "تا حالا دروغ بزرگ گفتی؟",
    "آخرین باری که خجالت کشیدی کی بود؟"
]

dares = [
    "10 بار بالا و پایین بپر",
    "تا 1 دقیقه نخند",
    "یک جوک تعریف کن",
    "به یک دوست پیام سلام بفرست",
    "5 شنا برو"
]

def send_message(chat_id, text, reply_to=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_to is not None:
        data["reply_to_message_id"] = reply_to

    try:
        requests.post(
            f"{BASE_URL}/sendMessage",
            json=data,
            timeout=10
        )
    except:
        pass

def match_command(text):
    commands = [
        "سلام",
        "خوبی",
        "صبح بخیر",
        "شب بخیر",
        "چالش",
        "تاس",
        "شیر یا خط",
        "عدد شانسی",
        "حقیقت",
        "جرئت"
    ]

    result = get_close_matches(
        text,
        commands,
        n=1,
        cutoff=0.65
    )

    if result:
        return result[0]

    return text

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

            matched_text = match_command(text)

            # بازی ها

            if matched_text == "چالش":
                send_message(
                    chat_id,
                    f"🎯 چالش:\n\n{random.choice(challenges)}",
                    reply_to=message_id
                )
                continue

            if matched_text == "تاس":
                send_message(
                    chat_id,
                    f"🎲 عدد تاس: {random.randint(1,6)}",
                    reply_to=message_id
                )
                continue

            if matched_text == "شیر یا خط":
                send_message(
                    chat_id,
                    f"🪙 {random.choice(['شیر','خط'])}",
                    reply_to=message_id
                )
                continue

            if matched_text == "عدد شانسی":
                send_message(
                    chat_id,
                    f"🔢 عدد شانسی شما: {random.randint(1,100)}",
                    reply_to=message_id
                )
                continue

            if matched_text == "حقیقت":
                send_message(
                    chat_id,
                    f"🎤 حقیقت:\n{random.choice(truths)}",
                    reply_to=message_id
                )
                continue

            if matched_text == "جرئت":
                send_message(
                    chat_id,
                    f"🔥 جرئت:\n{random.choice(dares)}",
                    reply_to=message_id
                )
                continue

            # دستورات ادمین

            if user_id == OWNER_ID:

                if text == "بخواب":
                    BOT_ENABLED = False
                    send_message(
                        chat_id,
                        "اخ جوون من خوابیدم 😴😍",
                        reply_to=message_id
                    )
                    continue

                if text == "بیدارشو":
                    BOT_ENABLED = True
                    send_message(
                        chat_id,
                        "ای ملعون چرا بیدارم میکنی 🤬",
                        reply_to=message_id
                    )
                    continue

            # خاموش بودن ربات

            if not BOT_ENABLED and user_id != OWNER_ID:
                continue

            # پاسخ ادمین

            if user_id == OWNER_ID:

                reply = owner_answers.get(
                    matched_text,
                    "چی چی میگویی ملعون؟ 😈"
                )

            # کاربران عادی

            else:

                if text == "/start":
                    reply = (
                        "سلام 👋\n"
                        "به ربات خوش آمدید\n\n"
                        "🎮 دستورات:\n"
                        "چالش\n"
                        "تاس\n"
                        "شیر یا خط\n"
                        "عدد شانسی\n"
                        "حقیقت\n"
                        "جرئت"
                    )

                elif matched_text == "سلام":
                    reply = "سلام 👋"

                elif matched_text == "خوبی":
                    reply = "ممنون، خوبم 😊"

                elif matched_text == "صبح بخیر":
                    reply = "صبح شما هم بخیر ☀️"

                elif matched_text == "شب بخیر":
                    reply = "شب شما هم بخیر 🌙"

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
