import requests
import time

TOKEN = "1597508244:loyNgb9a1cdwlgLxF9ln7sofuwhYOjFN7Xk"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0
processed = set()  # جلوگیری قطعی از تکرار


def send_message(chat_id, text):
    requests.post(
        f"{BASE_URL}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=10
    )


print("🚀 Bot Started")

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

            update_id = update.get("update_id")

            # 🔥 جلوگیری قطعی از دوبار پردازش
            if update_id in processed:
                continue

            processed.add(update_id)

            # ✔ فقط اینجا offset جلو میره
            offset = update_id + 1

            message = update.get("message")
            if not message:
                continue

            chat_id = message["chat"]["id"]
            text = message.get("text", "")

            print("USER:", text)

            if text == "/start":
                send_message(chat_id, "سلام 👋")

            elif text == "سلام":
                send_message(chat_id, "سلام خوبی؟")

            else:
                send_message(chat_id, "❓")

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
