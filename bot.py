import os
import time
import requests
import psycopg2

BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")

offset = 0

user_state = {}


# ---------------- DB ----------------
def db():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        user_id TEXT,
        text TEXT,
        status TEXT DEFAULT 'NEW'
    )
    """)

    conn.commit()
    cur.close()
    conn.close()


init_db()


# ---------------- BOT API ----------------
def send(chat_id, text):
    url = f"https://tapi.bale.ai/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": text
    })


def get_updates(offset):
    url = f"https://tapi.bale.ai/bot{BOT_TOKEN}/getUpdates"
    r = requests.get(url, params={"offset": offset, "timeout": 10})
    return r.json().get("result", [])


# ---------------- SAVE ORDER ----------------
def save_order(user_id, text):
    conn = db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO orders(user_id,text) VALUES(%s,%s)",
        (user_id, text)
    )

    conn.commit()
    cur.close()
    conn.close()


# ---------------- MAIN LOOP ----------------
def run():
    global offset

    print("Bot started...")

    while True:

        updates = get_updates(offset)

        for u in updates:

            offset = u["update_id"] + 1

            if "message" not in u:
                continue

            msg = u["message"]
            chat_id = str(msg["chat"]["id"])
            text = msg.get("text", "")

            if text == "/start":
                send(chat_id,
"""
🏢 CRM بیمه

پیام بده برای ثبت سفارش:
نام - شماره - نوع بیمه
"""
                )

            else:
                save_order(chat_id, text)

                send(chat_id,
"✅ سفارش ثبت شد. کارشناسان با شما تماس می‌گیرند."
                )

        time.sleep(1)


if __name__ == "__main__":
    run()
