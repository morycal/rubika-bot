import requests
import time
from datetime import datetime
import random

TOKEN = "1597508244:loyNgb9a1cdwlgLxF9ln7sofuwhYOjFN7Xk"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0


# ---------------- پاسخ‌های صمیمی ----------------
greetings = [
    "سلام 😄 خوش اومدی!",
    "سلام رفیق 👋 چطوری؟",
    "هلووو 😎 چه خبر؟",
    "سلام! دلم برات تنگ شده بود 😆"
]

how_are_you = [
    "خوبم مرسی 🙂 تو چطوری؟",
    "عالی‌ام 😄 فقط یه کم باگ دارم مثل همه 😆",
    "رو به راهم 👌 تو چی؟",
    "زنده‌ام 😄 همین خودش کافیه!"
]

what_doing = [
    "هیچی خاص 😄 دارم با تو چت می‌کنم",
    "دارم فکر می‌کنم چرا کد من همیشه درست کار نمی‌کنه 😂",
    "منتظرم تو چیزی بگی 😎",
    "در حال لذت بردن از زندگی دیجیتال 🤖"
]

goodbye = [
    "فعلاً 👋 مراقب خودت باش 😄",
    "بای بای 😎 زود برگرد",
    "خدافظ رفیق ❤️",
    "می‌بینمت 👋"
]


def send_message(chat_id, text):
    try:
        requests.post(
            f"{BASE_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10
        )
    except Exception as e:
        print("SEND ERROR:", e)


print("🚀 Friendly Bot Started")

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

            print("USER:", text)

            # ---------------- HANDLING ----------------

            if text == "/start":
                send_message(chat_id,
                    "🤖 سلام رفیق!\n"
                    "من یه بات ساده ولی صمیمی‌ام 😄\n\n"
                    "📌 می‌تونی بپرسی:\n"
                    "سلام\n"
                    "خوبی\n"
                    "چیکار می‌کنی\n"
                    "بای\n"
                    "time"
                )

            elif "سلام" in text or "hello" in text:
                send_message(chat_id, random.choice(greetings))

            elif "خوبی" in text or "how are you" in text:
                send_message(chat_id, random.choice(how_are_you))

            elif "چیکار میکنی" in text or "چی کار میکنی" in text:
                send_message(chat_id, random.choice(what_doing))

            elif "بای" in text or "خدافظ" in text:
                send_message(chat_id, random.choice(goodbye))

            elif text == "تاریخ":
                now = datetime.now().strftime("%Y-%m-%d ⏰ %H:%M:%S")
                send_message(chat_id,
                    f"⏰ ساعت الان:\n{now}\n"
                    "وقتشه یه استراحت کوچیک بدی 😄"
                )

            else:
                send_message(chat_id,
                    "😅 راستش اینو درست نفهمیدم...\n"
                    "ولی دارم یاد می‌گیرم 😎"
                )

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
