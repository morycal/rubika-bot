import requests
import time
import os

TOKEN = os.getenv("RUBIKA_TOKEN")
if not TOKEN:
    raise Exception("RUBIKA_TOKEN is not set!")

BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

offset = None


# ---------------- SEND MESSAGE ----------------
def send_message(chat_id, text):

    try:
        res = requests.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text
            },
            timeout=10
        )

        print("SEND:", res.text)

    except Exception as e:
        print("SEND ERROR:", e)


# ---------------- MAIN LOOP ----------------
print("🚀 Simple Bot Started")

while True:

    try:
        payload = {}

        if offset:
            payload["offset_id"] = offset

        res = requests.post(
            f"{BASE_URL}/getUpdates",
            json=payload,
            timeout=15
        )

        data = res.json()

        if data.get("status") != "OK":
            time.sleep(1)
            continue

        updates = data["data"]["updates"]

        for u in updates:

            offset = u.get("update_time")

            if u.get("type") != "NewMessage":
                continue

            msg = u.get("new_message", {})
            text = msg.get("text", "")

            chat_id = u.get("chat_id")

            if not chat_id:
                continue

            print("USER:", text)

            # ---------------- COMMANDS ----------------
            if text == "/start":
                send_message(chat_id, "🤖 سلام! بات فعال شد")

            elif text == "سلام":
                send_message(chat_id, "👋 سلام عزیز!")

            elif text == "خوبی":
                send_message(chat_id, "🙂 خوبم مرسی")

            elif text == "help":
                send_message(chat_id, "📌 دستورات: /start - سلام - خوبی - help")

            else:
                send_message(chat_id, "❓ دستور ناشناخته")

    except Exception as e:
        print("LOOP ERROR:", e)
        time.sleep(2)

    time.sleep(1)
