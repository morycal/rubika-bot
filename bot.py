import os
import requests
import time
from db import conn

BOT_TOKEN = os.environ.get("BOT_TOKEN")

offset = 0


def send(chat_id, text):
    url = f"https://tapi.bale.ai/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})


def get_updates():
    global offset
    url = f"https://tapi.bale.ai/bot{BOT_TOKEN}/getUpdates"
    r = requests.get(url, params={"offset": offset})
    return r.json().get("result", [])


def save_order(user_id, text):
    c = conn()
    cur = c.cursor()

    cur.execute(
        "INSERT INTO orders(user_id,text,status) VALUES(%s,%s,'NEW')",
        (user_id, text)
    )

    c.commit()
    cur.close()
    c.close()


while True:

    updates = get_updates()

    for u in updates:

        offset = u["update_id"] + 1

        if "message" not in u:
            continue

        msg = u["message"]
        chat_id = str(msg["chat"]["id"])
        text = msg.get("text", "")

        if text == "/start":
            send(chat_id, "📦 سفارش بیمه را ارسال کنید")

        else:
            save_order(chat_id, text)
            send(chat_id, "✅ ثبت شد")

    time.sleep(1)
