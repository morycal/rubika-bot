import requests
import time

TOKEN = "YOUR_BALE_TOKEN"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

OWNER_ID = 123456789  # آیدی خودت

last_update_id = 0

owner_answers = {
"سلام": "سلام سرورم ❤️",
"سلامم": "سلام سرور عزیزم ❤️",
"خوبی": "ممنون سرورم، شما خوبی؟ 👑",
"چطوری": "عالی‌ام سرورم، شما چطوری؟ 😊",
"صبح بخیر": "صبح شما بخیر سرورم ☀️❤️",
"ظهر بخیر": "ظهرتون بخیر سرورم 🌷",
"عصر بخیر": "عصر بخیر سرورم 🌹",
"شب بخیر": "شب شما هم بخیر سرورم 🌙❤️",
"خسته نباشی": "فدای شما سرورم ❤️",
"مرسی": "قربان شما سرورم 🌹",
"ممنون": "خواهش می‌کنم سرورم ❤️",
"چه خبر": "سلامتی سرورم، خبر خاصی نیست 😊",
"بیداری": "بله سرورم، در خدمتم 👑",
"هستی": "همیشه در خدمت سرورم ❤️",
"آنلاینی": "بله سرورم، آنلاینم 👑",
"ربات": "جانم سرورم؟ ❤️",
"دوستم داری": "البته سرورم ❤️👑",
"روز بخیر": "روز شما بخیر سرورم 🌹",
"عاشقتم": "منم دوستت دارم سرورم ❤️",
"خدانگهدار": "خدا نگهدار سرورم ❤️",
"بای": "فعلاً سرورم 👋❤️",
"خوابم میاد": "استراحت کن سرورم 😴❤️",
"کمکم کن": "حتماً سرورم، بفرمایید 👑",
"جواب بده": "در خدمتم سرورم ❤️",
"عالی": "خوشحالم سرورم 🌹",
"دمت گرم": "فدای شما سرورم ❤️",
"قربونت": "قربان شما سرورم 👑❤️"
}

def send_message(chat_id, text, reply_to=None):
data = {
"chat_id": chat_id,
"text": text
}

```
if reply_to:
    data["reply_to_message_id"] = reply_to

requests.post(
    f"{BASE_URL}/sendMessage",
    json=data
)
```

while True:
try:
response = requests.get(
f"{BASE_URL}/getUpdates",
params={"offset": last_update_id + 1}
).json()

```
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

        # پاسخ مخصوص صاحب ربات
        if user_id == OWNER_ID:

            if text in owner_answers:
                reply = owner_answers[text]
            else:
                reply = f"بفرمایید سرورم 👑\n{text}"

        # پاسخ کاربران عادی
        else:

            if text == "/start":
                reply = "سلام 👋\nبه ربات خوش آمدید."

            elif text == "سلام":
                reply = "سلام 👋"

            elif text == "خوبی":
                reply = "ممنون، خوبم 😊"

            elif text == "شب بخیر":
                reply = "شب شما هم بخیر 🌙"

            elif text == "صبح بخیر":
                reply = "صبح شما هم بخیر ☀️"

            else:
                reply = f"شما گفتید:\n{text}"

        send_message(
            chat_id,
            reply,
            reply_to=message_id
        )

    time.sleep(1)

except Exception as e:
    print("ERROR:", e)
    time.sleep(5)
```
