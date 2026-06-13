import requests
import time

TOKEN = "YOUR_BALE_BOT_TOKEN"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0
seen = set()  # جلوگیری از تکرار


def send_message(chat_id, text):
    try:
        requests.post(
            f"{BASE_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10
        )
    except Exception as e:
        print("SEND ERROR:", e)


print("🚀 Bale Bot Started")

while True:

    try:
        res = requests.post(
            f"{BASE_URL}/getUpdates",
            json={"offset": offset},
            timeout=15
        )

        data = res.json()

        if not data.get("ok"):
            time.sleep(1)
            continue

        updates = data.get("result", [])

        for update in updates:

            update_id = update["update_id"]

            # ⛔ جلوگیری از دوبار پردازش
            if update_id in seen:
                continue

            seen.add(update_id)

            message = update.get("message")
            if not message:
                continue

            chat_id = message["chat"]["id"]
            text = message.get("text", "")

            print("USER:", text)

            if text == "/start":
                send_message(chat_id, "🤖 ربات فعال شد!")

            elif text == "سلام":
                send_message(chat_id, "👋 سلام!")

            else:
                send_message(chat_id, "❓ دستور ناشناخته")

            # ✔ اینجا offset را درست جلو ببر
            offset = update_id + 1

    except Exception as e:
        print("LOOP ERROR:", e)
        time.sleep(2)

    time.sleep(1)
