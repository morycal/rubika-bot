import requests
import time
import random

TOKEN = "1597508244:uHdj4lnrEAz6lENe0GQI6cUltRiW3ogrNeY"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0

# ---------------- GAME STATE ----------------

games = {}

# ---------------- DATA ----------------

quiz_questions = [
    ("پایتخت ایران؟", "تهران"),
    ("2+2؟", "4"),
    ("3×3؟", "9"),
    ("آب چند درجه یخ می‌زند؟", "0"),
    ("پایتخت ترکیه؟", "آنکارا"),
    ("رنگ آسمان؟", "آبی"),
    ("پایتخت فرانسه؟", "پاریس"),
    ("5+7؟", "12"),
    ("10-3؟", "7"),
    ("ماه چند تاست؟", "1"),
]

dare_list = [
    "😂 یه ایموجی خنده بفرست",
    "📢 یه سلام بلند بگو",
    "😆 عدد 1 تا 10 انتخاب کن",
    "🎤 یه کلمه انگلیسی بگو",
    "🤡 خودتو توصیف کن",
    "📸 یه چیز بامزه بنویس",
    "🔥 بگو من خفنم 😎",
    "🙈 یه جمله خجالت‌آور بگو",
]

truth_list = [
    "💬 بزرگترین ترست چیه؟",
    "💬 عاشق شدی تا حالا؟",
    "💬 بهترین دوستت کیه؟",
    "💬 دروغ گفتی امروز؟",
    "💬 بزرگترین رازت چیه؟",
    "💬 از چی بیشتر بدت میاد؟",
    "💬 آخرین باری که گریه کردی کی بود؟",
]

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

# ---------------- MAIN MENU ----------------

def main_menu():

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

# ---------------- RPS MENU ----------------

def rps_menu():

    return {
        "inline_keyboard": [
            [
                {"text": "✊ سنگ", "callback_data": "rps_sang"},
                {"text": "✋ کاغذ", "callback_data": "rps_kaghaz"},
                {"text": "✌️ قیچی", "callback_data": "rps_ghichi"}
            ]
        ]
    }

# ---------------- TIC TAC TOE MENU ----------------

def tic_menu():

    return {
        "inline_keyboard": [
            [
                {"text": "1", "callback_data": "tic_1"},
                {"text": "2", "callback_data": "tic_2"},
                {"text": "3", "callback_data": "tic_3"}
            ],
            [
                {"text": "4", "callback_data": "tic_4"},
                {"text": "5", "callback_data": "tic_5"},
                {"text": "6", "callback_data": "tic_6"}
            ],
            [
                {"text": "7", "callback_data": "tic_7"},
                {"text": "8", "callback_data": "tic_8"},
                {"text": "9", "callback_data": "tic_9"}
            ]
        ]
    }

# ---------------- BOT ----------------

print("🚀 GAME PRO BOT STARTED")

while True:

    try:

        updates = requests.post(
            f"{BASE_URL}/getUpdates",
            json={"offset": offset},
            timeout=15
        ).json()

        for update in updates.get("result", []):

            offset = update["update_id"] + 1

            # ---------------- MESSAGE ----------------

            if "message" in update:

                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "")
                mid = msg.get("message_id")

                if text == "/start":
                    send_message(chat_id,
                        "🎮 سلام!\n\nبرای شروع بنویس: بازی",
                        mid
                    )

                elif text == "بازی":
                    send_message(chat_id,
                        "🎮 بازی رو انتخاب کن:",
                        mid,
                        main_menu()
                    )

            # ---------------- CALLBACK ----------------

            if "callback_query" in update:

                cb = update["callback_query"]
                data = cb["data"]
                chat_id = cb["message"]["chat"]["id"]

                # ---------------- MENU ----------------

                if data == "quiz":

                    q = random.choice(quiz_questions)
                    games[chat_id] = {"type": "quiz", "ans": q[1]}

                    send_message(chat_id, f"🧠 سوال:\n{q[0]}")

                elif data == "dare":

                    send_message(chat_id,
                        "🎯 جرئت و حقیقت:\n" +
                        random.choice(dare_list + truth_list)
                    )

                elif data == "rps":

                    send_message(chat_id,
                        "✊ یکی رو انتخاب کن:",
                        keyboard=rps_menu()
                    )

                elif data == "tic":

                    games[chat_id] = {
                        "board": ["1","2","3","4","5","6","7","8","9"]
                    }

                    send_message(chat_id,
                        "⭕ دوز شروع شد!\nیک خانه انتخاب کن:",
                        keyboard=tic_menu()
                    )

                # ---------------- RPS ----------------

                elif data.startswith("rps_"):

                    bot = random.choice(["سنگ","کاغذ","قیچی"])
                    user = data.split("_")[1]

                    map_rps = {
                        "sang": "سنگ",
                        "kaghaz": "کاغذ",
                        "ghichi": "قیچی"
                    }

                    user = map_rps[user]

                    if user == bot:
                        res = "مساوی 😐"
                    elif (user=="سنگ" and bot=="قیچی") or \
                         (user=="کاغذ" and bot=="سنگ") or \
                         (user=="قیچی" and bot=="کاغذ"):
                        res = "تو بردی 🎉"
                    else:
                        res = "باختی 😆"

                    send_message(chat_id,
                        f"✊ تو: {user}\n🤖 من: {bot}\n📊 {res}"
                    )

                # ---------------- TIC TAC TOE ----------------

                elif data.startswith("tic_"):

                    pos = int(data.split("_")[1]) - 1

                    if chat_id not in games:
                        send_message(chat_id, "❌ بازی شروع نشده")
                        continue

                    board = games[chat_id]["board"]

                    if board[pos] in ["X","O"]:
                        send_message(chat_id, "❌ این خونه پره")
                        continue

                    board[pos] = "X"

                    bot_move = random.choice([i for i in range(9) if board[i] not in ["X","O"]])
                    board[bot_move] = "O"

                    send_message(chat_id,
                        f"""
⭕ دوز:

{board[0]} | {board[1]} | {board[2]}
{board[3]} | {board[4]} | {board[5]}
{board[6]} | {board[7]} | {board[8]}
""",
                        keyboard=tic_menu()
                    )

            # ---------------- QUIZ ANSWER ----------------

            if "message" in update:

                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text","")

                if chat_id in games and games[chat_id]["type"] == "quiz":

                    if text == games[chat_id]["ans"]:
                        send_message(chat_id, "🎉 درست!")
                    else:
                        send_message(chat_id, f"❌ غلط! جواب: {games[chat_id]['ans']}")

                    games.pop(chat_id, None)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
