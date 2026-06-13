import requests
import time

TOKEN = "1597508244:loyNgb9a1cdwlgLxF9ln7sofuwhYOjFN7Xk"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0


def send_message(chat_id, text):
    try:
        requests.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text
            },
            timeout=10
        )
    except Exception as e:
        print("SEND ERROR:", e)


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

            # جلو بردن offset فقط یکبار
            offset = update_id + 1

            message = update.get("message")
            if not message:
                continue

            chat_id = message["chat"]["id"]
            text = message.get("text", "")

            print("USER:", text)

            # ---------------- COMMANDS ----------------
            if text == "/start":
                send_message(chat_id, "🤖 سلام! بات فعاله")

            elif text == "سلام":
                send_message(chat_id, "👋 سلام!")

            elif text == "خوبی":
                send_message(chat_id, "🙂 خوبم مرسی")

            else:
                send_message(chat_id, "❓ دستور ناشناخته")

    except Exception as e:
        print("LOOP ERROR:", e)
        time.sleep(2)

    time.sleep(1)
