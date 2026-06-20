import requests
import time

TOKEN = "1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

OWNER_ID = 586110315
last_update_id = 0

owner_answers = {
    "سلام": "سلام ملعون بزرگ ",
    "خوبی": "فدات ملعون ، تو هم که همیشه خوبی 😂",
    "چطوری": "عالی‌ام ملعون 😊",
    "صبح بخیر": "صبح شما بخیر مارمولک ☀️",
     "شب بخیر": "شب شما هم بخیر ملعون اعظم 🌙",
    "مرسی": "قربان شما  ❤️",
    "ممنون": "خواهش می‌کنم خوابالو ❤️",
    "چه خبر": "سلامتی ترنک 😊"
}

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

            if user_id == OWNER_ID:
                reply = owner_answers.get(
                    text,
                    f"\nچی چی میگویی ملعون؟"
                )
            else:
                if text == "/start":
                    reply = "سلام 👋\nبه ربات خوش آمدید"
                elif text == "سلام":
                    reply = "سلام 👋"
                elif text == "خوبی":
                    reply = "ممنون، خوبم 😊"
                else:
                    reply = f"\nهااان؟؟"

            send_message(
                chat_id,
                reply,
                reply_to=message_id
            )

        time.sleep(1)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)
