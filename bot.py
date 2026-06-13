import requests
import time
from datetime import datetime
import random

TOKEN = "1597508244:uHdj4lnrEAz6lENe0GQI6cUltRiW3ogrNeY"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0


# ---------------- پاسخ‌های صمیمی ----------------
greetings = [
    "سلام 😄 خوش اومدی!",
    "هلووو 👋 چه خبر؟",
    "سلام رفیق 😎 حالت چطوره؟",
    "سلام! بالاخره اومدی 😆"
]

how_are_you = [
    "خوبم مرسی 🙂 تو چطوری؟",
    "عالی‌ام 😄 تو چی؟",
    "رو به راهم 👌 تو چطور؟",
    "زنده‌ام 😆 همین کافیه!"
]

chitchat = [
    "دارم با تو چت می‌کنم 😄",
    "هیچی خاص، منتظر پیام بعدی توام 😎",
    "دارم فکر می‌کنم چرا دنیا اینقدر باگ داره 😂",
    "در حال استراحت دیجیتالی 🤖"
]

goodbye = [
    "فعلاً 👋 مراقب خودت باش 😄",
    "بای بای 😎 زود برگرد",
    "خدافظ رفیق ❤️",
    "می‌بینمت 👋"
]


# ---------------- send message ----------------
def send_message(chat_id, text, reply_to=None):
    try:
        payload = {
            "chat_id": chat_id,
            "text": text
        }

        # 👉 ریپلای واقعی
        if reply_to:
            payload["reply_to_message_id"] = reply_to

        requests.post(
            f"{BASE_URL}/sendMessage",
            json=payload,
            timeout=10
        )

    except Exception as e:
        print("SEND ERROR:", e)


print("🚀 Friendly Reply Bot Started")

# ---------------- main loop ----------------
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
            offset = update_id + 1

            message = update.get("message")
            if not message:
                continue

            chat_id = message["chat"]["id"]
            text = message.get("text", "").lower()
            message_id = message.get("message_id")

            print("USER:", text)

            # ---------------- COMMANDS ----------------

            if text == "/start":
                send_message(
                    chat_id,
                    "🤖 سلام رفیق!\n"
                    "من یه بات صمیمی‌ام 😄\n\n"
                    "📌 امتحان کن:\n"
                    "سلام\n"
                    "خوبی\n"
                    "چیکار می‌کنی\n"
                    "time\n"
                    "بای",
                    reply_to=message_id
                )

            elif "سلام" in text:
                send_message(chat_id, random.choice(greetings), reply_to=message_id)

            elif "خوبی" in text or "how are you" in text:
                send_message(chat_id, random.choice(how_are_you), reply_to=message_id)

            elif "چیکار میکنی" in text or "چی کار میکنی" in text:
                send_message(chat_id, random.choice(chitchat), reply_to=message_id)

            elif "بای" in text or "خدافظ" in text:
                send_message(chat_id, random.choice(goodbye), reply_to=message_id)

            elif text == "زمان":
                now = datetime.now().strftime("%Y-%m-%d ⏰ %H:%M:%S")
                send_message(
                    chat_id,
                    f"⏰ الان این ساعتشه:\n{now}\n"
                    "وقتشه یه استراحت کوچیک بدی 😄",
                    reply_to=message_id
                )

           

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
