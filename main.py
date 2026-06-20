import requests
import time

TOKEN = "1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

OWNER_ID = 586110315
last_update_id = 0

owner_answers = {
    "سلام": "سلام سرورم ❤️",
    "خوبی": "ممنون سرورم، شما خوبی؟ 👑",
    "چطوری": "عالی‌ام سرورم 😊",
    "صبح بخیر": "صبح شما بخیر سرورم ☀️",
    "شب بخیر": "شب شما هم بخیر سرورم 🌙"
}


def send_message(chat_id, text):
    requests.post(
        f"{BASE_URL}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text
        }
    )


while True:
    try:
        response = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": last_update_id + 1}
        ).json()

        for update in response.get("result", []):

            last_update_id = update["update_id"]

            if "message" not in update:
                continue

            message = update["message"]

            chat_id = message["chat"]["id"]
            user_id = message["from"]["id"]

            text = message.get("text", "").strip()

            if not text:
                continue

            if user_id == OWNER_ID:
                reply = owner_answers.get(
                    text,
                    f"بفرمایید سرورم 👑\n{text}"
                )
            else:
                if text == "/start":
                    reply = "سلام 👋 به ربات خوش آمدید"
                else:
                    reply = f"شما گفتید:\n{text}"

            send_message(chat_id, reply)

        time.sleep(1)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)
