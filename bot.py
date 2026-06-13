import requests
import time

TOKEN = "1597508244:loyNgb9a1cdwlgLxF9ln7sofuwhYOjFN7Xk"

BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0


# ---------------- SEND MESSAGE ----------------
def send_message(chat_id, text):
    try:
        url = f"{BASE_URL}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text
        }

        res = requests.post(url, json=payload, timeout=10)
        print("SEND:", res.text)

    except Exception as e:
        print("SEND ERROR:", e)


# ---------------- GET UPDATES ----------------
print("🚀 Bale Bot Started")

while True:

    try:
        url = f"{BASE_URL}/getUpdates"

        res = requests.post(url, json={"offset": offset})
        data = res.json()

        if not data.get("ok"):
            time.sleep(1)
            continue

        for update in data.get("result", []):

            offset = update["update_id"] + 1

            message = update.get("message")
            if not message:
                continue

            chat_id = message["chat"]["id"]
            text = message.get("text", "")

            print("USER:", text)

            # ---------------- COMMANDS ----------------
            if text == "/start":
                send_message(chat_id, "🤖 ربات بله فعال شد!")

            elif text == "سلام":
                send_message(chat_id, "👋 سلام! خوبی؟")

            elif text == "خوبی":
                send_message(chat_id, "🙂 خوبم مرسی")

            elif text == "help":
                send_message(chat_id, "📌 دستورات:\n/start\nسلام\nخوبی\nhelp")

            else:
                send_message(chat_id, "❓ دستور ناشناخته")

    except Exception as e:
        print("LOOP ERROR:", e)
        time.sleep(2)

    time.sleep(1)
