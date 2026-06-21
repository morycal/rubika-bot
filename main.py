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
        json={"chat_id": chat_id, "text": text[:4000]},
        timeout=30
    )


def get_user(user_id):
    cur.execute("SELECT questions, vip_until FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()

    if not row:
        cur.execute(
            "INSERT INTO users(user_id, questions, vip_until) VALUES(?,?,?)",
            (user_id, 0, 0)
        )
        db.commit()
        return 0, 0

    return row


def add_question(user_id):
    cur.execute("UPDATE users SET questions = questions + 1 WHERE user_id=?", (user_id,))
    db.commit()


def activate_vip(user_id):
    vip_until = int(time.time()) + (30 * 24 * 60 * 60)

    cur.execute(
        "UPDATE users SET vip_until=? WHERE user_id=?",
        (vip_until, user_id)
    )
    db.commit()


def deactivate_vip(user_id):
    cur.execute(
        "UPDATE users SET vip_until=0 WHERE user_id=?",
        (user_id,)
    )
    db.commit()


def can_use(user_id):
    questions, vip_until = get_user(user_id)

    if vip_until > int(time.time()):
        return True

    return questions < 3


def ask_ai(text):
    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen3-8B",
            messages=[
                {"role": "system", "content": "تو یک دستیار فارسی هستی."},
                {"role": "user", "content": text}
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
            params={"offset": offset, "timeout": 30},
            timeout=35
        ).json()

        for update in updates.get("result", []):
            offset = update["update_id"] + 1

            if "message" not in update:
                continue

            message = update["message"]

            chat_id = message["chat"]["id"]
            user_id = message["from"]["id"]
            text = message.get("text", "").strip()

            if not text:
                continue

            # start
            if text == "/start":
                send_message(
                    chat_id,
                    f"سلام 👋\n۳ سوال رایگان داری.\n"
                    f"ادمین: {ADMIN_ID}"
                )
                continue

            # status
            if text == "/status":
                q, vip = get_user(user_id)

                if vip > int(time.time()):
                    send_message(chat_id, "✅ اشتراک فعال است")
                else:
                    send_message(chat_id, f"سوال باقی‌مانده: {max(0, 3 - q)}")

                continue

            # VIP activate
            if user_id == ADMIN_ID and text.startswith("/vip"):
                parts = text.split()

                if len(parts) != 2:
                    send_message(chat_id, "مثال: /vip 123456789")
                    continue

                target = int(parts[1])

                get_user(target)
                activate_vip(target)

                send_message(chat_id, f"VIP فعال شد برای {target}")
                send_message(target, "✅ اشتراک شما فعال شد")

                continue

            # VIP deactivate ⭐ NEW
            if user_id == ADMIN_ID and text.startswith("/unvip"):
                parts = text.split()

                if len(parts) != 2:
                    send_message(chat_id, "مثال: /unvip 123456789")
                    continue

                target = int(parts[1])

                get_user(target)
                deactivate_vip(target)

                send_message(chat_id, f"VIP غیرفعال شد برای {target}")
                send_message(target, "❌ اشتراک شما غیرفعال شد")

                continue

            # check access
            if not can_use(user_id):
                send_message(
                    chat_id,
                    f"❌ اتمام اعتبار\n"
                    f"با ادمین هماهنگ کنید\nID: {ADMIN_ID}"
                )
                continue

            # increase usage
            q, vip = get_user(user_id)
            if vip < int(time.time()):
                add_question(user_id)

            answer = ask_ai(text)
            send_message(chat_id, answer)

    except Exception as e:
        print(e)
        time.sleep(5)
