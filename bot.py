import requests
import time
import random

TOKEN = "1597508244:uHdj4lnrEAz6lENe0GQI6cUltRiW3ogrNeY"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0

# ---------------- GAME STATE ----------------

games = {}

# ---------------- SEND ----------------

def send_message(chat_id, text, reply_to=None, keyboard=None):

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_to:
        payload["reply_to_message_id"] = reply_to

    if keyboard:
        payload["reply_markup"] = keyboard

    try:
        requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
    except:
        pass

# ---------------- MENU KEYBOARD ----------------

def game_menu():

    return {
        "inline_keyboard": [
            [
                {"text": "🎯 جرئت و حقیقت", "callback_data": "dare"},
                {"text": "🧠 کوئیز", "callback_data": "quiz"}
            ],
            [
                {"text": "✊ سنگ کاغذ قیچی", "callback_data": "rps"}
            ],
            [
                {"text": "⭕ دوز", "callback_data": "tic"}
            ]
        ]
    }

# ---------------- QUIZ ----------------

quiz_questions = [
    ("پایتخت ایران؟", "تهران"),
    ("2+2؟", "4"),
    ("آب چند درجه یخ می‌زند؟", "0"),
]

# ---------------- LOOP ----------------

print("🚀 GAME MENU BOT STARTED")

while True:

    try:

        updates = requests.post(
            f"{BASE_URL}/getUpdates",
            json={"offset": offset},
            timeout=15
        ).json()

        for update in updates.get("result", []):

            offset = update["update_id"] + 1

            if "message" in update:

                msg = update["message"]

                chat_id = msg["chat"]["id"]
                text = msg.get("text", "")
                mid = msg.get("message_id")

                # ---------------- START ----------------

                if text == "/start":

                    send_message(
                        chat_id,
                        "🎮 سلام!\n\nبرای شروع بازی بنویس: بازی",
                        reply_to=mid
                    )

                # ---------------- GAME MENU ----------------

                elif text == "بازی":

                    send_message(
                        chat_id,
                        "🎮 یکی از بازی‌ها رو انتخاب کن:",
                        reply_to=mid,
                        keyboard=game_menu()
                    )

                # ---------------- CALLBACK (BUTTONS) ----------------

            if "callback_query" in update:

                cb = update["callback_query"]
                data = cb["data"]
                chat_id = cb["message"]["chat"]["id"]

                # -------- RPS --------

                if data == "rps":

                    games[chat_id] = {"type": "rps"}

                    send_message(chat_id,
                        "✊ یکی انتخاب کن:\nسنگ / کاغذ / قیچی"
                    )

                # -------- QUIZ --------

                elif data == "quiz":

                    q = random.choice(quiz_questions)

                    games[chat_id] = {"type": "quiz", "ans": q[1]}

                    send_message(chat_id, f"🧠 سوال:\n{q[0]}")

                # -------- DARE --------

                elif data == "dare":

                    dares = [
                        "😂 یه ایموجی بفرست",
                        "📢 یه سلام بلند بگو",
                        "😆 عدد 1 تا 10 انتخاب کن"
                    ]

                    send_message(chat_id, "🎯 جرئت:\n" + random.choice(dares))

                # -------- TIC TAC TOE --------

                elif data == "tic":

                    games[chat_id] = {
                        "board": ["1","2","3","4","5","6","7","8","9"]
                    }

                    b = games[chat_id]["board"]

                    send_message(chat_id,
                        f"""
⭕ دوز شروع شد:

{b[0]} | {b[1]} | {b[2]}
{b[3]} | {b[4]} | {b[5]}
{b[6]} | {b[7]} | {b[8]}

بگو شماره کجا بزنی
""")

            # ---------------- GAME ANSWERS ----------------

            if "message" in update:

                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text","")

                if chat_id in games:

                    g = games[chat_id]

                    # ---- RPS ----
                    if g["type"] == "rps":

                        bot = random.choice(["سنگ","کاغذ","قیچی"])

                        if text == bot:
                            res = "مساوی 😐"
                        elif (text=="سنگ" and bot=="قیچی") or \
                             (text=="کاغذ" and bot=="سنگ") or \
                             (text=="قیچی" and bot=="کاغذ"):
                            res = "تو بردی 🎉"
                        else:
                            res = "باختی 😆"

                        send_message(chat_id, f"🤖 من: {bot}\n📊 {res}")

                        games.pop(chat_id, None)

                    # ---- QUIZ ----
                    elif g["type"] == "quiz":

                        if text == g["ans"]:
                            send_message(chat_id, "🎉 درست!")
                        else:
                            send_message(chat_id, f"❌ غلط! جواب: {g['ans']}")

                        games.pop(chat_id, None)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
