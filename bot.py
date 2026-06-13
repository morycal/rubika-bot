import requests
import time
import random

TOKEN = "1597508244:uHdj4lnrEAz6lENe0GQI6cUltRiW3ogrNeY"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0

# ---------------- STATES ----------------

queue = {}
duels = {}
games = {}

# ---------------- DATA ----------------

quiz_questions = [
    ("2+2؟", "4"),
    ("پایتخت ایران؟", "تهران"),
    ("5×5؟", "25"),
    ("رنگ آسمان؟", "آبی"),
    ("10-3؟", "7"),
]

dare_list = [
    "😂 یه ایموجی بفرست",
    "📢 یه جمله خفن بگو",
]

# ---------------- SEND ----------------

def send(chat_id, text, keyboard=None):
    payload = {"chat_id": chat_id, "text": text}
    if keyboard:
        payload["reply_markup"] = keyboard

    try:
        requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
    except:
        pass

# ---------------- MENU ----------------

def menu():
    return {
        "inline_keyboard": [
            [
                {"text": "✊ دوئل سنگ/کاغذ/قیچی", "callback_data": "rps"},
                {"text": "🧠 دوئل کوئیز", "callback_data": "quiz"}
            ],
            [
                {"text": "⭕ دوئل دوز", "callback_data": "tic"}
            ]
        ]
    }

# ---------------- MATCHMAKING ----------------

def matchmake(chat_id, game_type):
    if game_type not in queue:
        queue[game_type] = []

    queue[game_type].append(chat_id)

    if len(queue[game_type]) < 2:
        send(chat_id, "⏳ منتظر حریف...", None)
        return None

    p1 = queue[game_type].pop(0)
    p2 = queue[game_type].pop(0)

    duel_id = str(random.randint(1000, 9999))

    duels[duel_id] = {
        "type": game_type,
        "p1": p1,
        "p2": p2,
        "turn": p1,
        "score": {p1: 0, p2: 0},
        "board": None
    }

    send(p1, "⚔️ حریف پیدا شد! شروع!", None)
    send(p2, "⚔️ حریف پیدا شد!", None)

    return duel_id

# ---------------- MAIN LOOP ----------------

print("🚀 DUEL BOT STARTED")

while True:

    try:
        updates = requests.post(
            f"{BASE_URL}/getUpdates",
            json={"offset": offset},
            timeout=15
        ).json()

        for u in updates.get("result", []):

            offset = u["update_id"] + 1

            # ---------------- MESSAGE ----------------

            if "message" in u:

                msg = u["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text","")
                mid = msg.get("message_id")

                if text == "/start":
                    send(chat_id, "🎮 وارد منو شو:", menu())

                elif text == "بازی":
                    send(chat_id, "🎮 انتخاب کن:", menu())

            # ---------------- CALLBACK ----------------

            if "callback_query" in u:

                cb = u["callback_query"]
                data = cb["data"]
                chat_id = cb["message"]["chat"]["id"]

                # ---------------- QUIZ DUEL ----------------

                if data == "quiz":

                    duel_id = matchmake(chat_id, "quiz")

                    if duel_id:
                        q = random.choice(quiz_questions)
                        duels[duel_id]["q"] = q[0]
                        duels[duel_id]["ans"] = q[1]

                        send(chat_id,
                            f"🧠 سوال:\n{q[0]}\nبنویس جواب:"
                        )

                # ---------------- RPS DUEL ----------------

                elif data == "rps":

                    matchmake(chat_id, "rps")

                    send(chat_id, "✊ بنویس: سنگ / کاغذ / قیچی")

                # ---------------- TIC TAC TOE DUEL ----------------

                elif data == "tic":

                    duel_id = matchmake(chat_id, "tic")

                    if duel_id:
                        duels[duel_id]["board"] = ["1","2","3","4","5","6","7","8","9"]

                        send(chat_id,
                            "⭕ دوز شروع شد!\nبگو شماره خانه"
                        )

            # ---------------- GAME LOGIC ----------------

            if "message" in u:

                msg = u["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text","")

                for duel_id, d in list(duels.items()):

                    if chat_id not in [d["p1"], d["p2"]]:
                        continue

                    enemy = d["p2"] if chat_id == d["p1"] else d["p1"]

                    # ---------------- QUIZ ----------------
                    if d["type"] == "quiz":

                        if text == d["ans"]:
                            d["score"][chat_id] += 1
                            send(chat_id, "🎉 درست!")
                        else:
                            send(chat_id, "❌ غلط!")

                        send(enemy, f"📊 امتیاز:\nP1: {d['score'][d['p1']]} | P2: {d['score'][d['p2']]}")

                        del duels[duel_id]

                    # ---------------- RPS ----------------
                    elif d["type"] == "rps":

                        bot = random.choice(["سنگ","کاغذ","قیچی"])

                        if text == bot:
                            res = "مساوی"
                        elif (text=="سنگ" and bot=="قیچی") or \
                             (text=="کاغذ" and bot=="سنگ") or \
                             (text=="قیچی" and bot=="کاغذ"):
                            res = "بردی"
                        else:
                            res = "باختی"

                        send(chat_id, f"🤖:{bot} → {res}")

                        del duels[duel_id]

                    # ---------------- TIC TAC TOE ----------------
                    elif d["type"] == "tic":

                        board = d["board"]

                        try:
                            pos = int(text) - 1
                        except:
                            continue

                        if pos < 0 or pos > 8:
                            continue

                        if board[pos] in ["X","O"]:
                            send(chat_id, "❌ پره")
                            continue

                        board[pos] = "X"

                        bot_move = random.choice([i for i in range(9) if board[i] not in ["X","O"]])
                        board[bot_move] = "O"

                        send(chat_id,
                            f"""
⭕ دوز:

{board[0]} | {board[1]} | {board[2]}
{board[3]} | {board[4]} | {board[5]}
{board[6]} | {board[7]} | {board[8]}
"""
                        )

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
