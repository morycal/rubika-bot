import os
import time
import sqlite3
import requests
from openai import OpenAI

BALE_TOKEN = os.getenv("BALE_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

ADMIN_ID = 586110315

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

BASE_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

db = sqlite3.connect("users.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    questions INTEGER DEFAULT 0,
    vip_until INTEGER DEFAULT 0
)
""")
db.commit()


def send_message(chat_id, text):
    requests.post(
        f"{BASE_URL}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text[:4000]
        },
        timeout=30
    )


def get_user(user_id):
    cur.execute(
        "SELECT questions,vip_until FROM users WHERE user_id=?",
        (user_id,)
    )

    row = cur.fetchone()

    if not row:
        cur.execute(
            "INSERT INTO users(user_id,questions,vip_until) VALUES(?,?,?)",
            (user_id, 0, 0)
        )
        db.commit()
        return 0, 0

    return row


def add_question(user_id):
    cur.execute(
        "UPDATE users SET questions=questions+1 WHERE user_id=?",
        (user_id,)
    )
    db.commit()


def activate_vip(user_id):
    vip_until = int(time.time()) + (30 * 24 * 60 * 60)

    cur.execute(
        "UPDATE users SET vip_until=? WHERE user_id=?",
        (vip_until, user_id)
    )
    db.commit()


def can_use(user_id):
    questions, vip_until = get_user(user_id)

    now = int(time.time())

    if vip_until > now:
        return True

    return questions < 3


def ask_ai(text):
    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen3-8B",
            messages=[
                {
                    "role": "system",
                    "content": "تو یک دستیار فارسی زبان مفید هستی."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            max_tokens=500
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"خطا: {e}"


offset = 0

print("Bot Started")

while True:
    try:
        updates = requests.get(
            f"{BASE_URL}/getUpdates",
            params={
                "offset": offset,
                "timeout": 30
            },
            timeout=35
        ).json()

        for update in updates.get("result", []):

            offset = update["update_id"] + 1

            if "message" not in update:
                continue

            message = update["message"]

            chat_id = message["chat"]["id"]
            text = message.get("text", "").strip()

            if not text:
                continue

            if text == "/start":
                send_message(
                    chat_id,
                    f"سلام 👋\n"
                    f"۳ سوال رایگان داری.\n"
                    f"بعد از اتمام اعتبار برای فعالسازی اشتراک ماهانه 10000 تومان با ادمین هماهنگ کن.\n\n"
                    f"آیدی ادمین:\n@ahmmad24"
                )
                continue

            if text == "/status":

                questions, vip_until = get_user(chat_id)

                if vip_until > int(time.time()):
                    days = (vip_until - int(time.time())) // 86400
                    send_message(
                        chat_id,
                        f"✅ اشتراک فعال\n"
                        f"روز باقی مانده: {days}"
                    )
                else:
                    remain = max(0, 3 - questions)

                    send_message(
                        chat_id,
                        f"سوال رایگان باقی مانده: {remain}"
                    )

                continue

            if chat_id == ADMIN_ID and text.startswith("/vip"):

                parts = text.split()

                if len(parts) != 2:
                    send_message(
                        chat_id,
                        "نمونه:\n/vip 123456789"
                    )
                    continue

                target_id = int(parts[1])

                get_user(target_id)
                activate_vip(target_id)

                send_message(
                    chat_id,
                    f"اشتراک کاربر {target_id} فعال شد."
                )

                send_message(
                    target_id,
                    "✅ اشتراک 30 روزه شما فعال شد."
                )

                continue

            if not can_use(chat_id):

                send_message(
                    chat_id,
                    "❌ اعتبار رایگان شما تمام شده است.\n\n"
                    "برای فعالسازی اشتراک ماهانه 10000 تومان با ادمین هماهنگ کنید.\n\n"
                    f"آیدی ادمین:\n@ahmmad24"
                )

                continue

            questions, vip_until = get_user(chat_id)

            if vip_until < int(time.time()):
                add_question(chat_id)

            answer = ask_ai(text)

            send_message(chat_id, answer)

    except Exception as e:
        print(e)
        time.sleep(5)
