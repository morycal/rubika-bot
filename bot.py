import requests
import time
import random
import threading

TOKEN = "YOUR_BALE_TOKEN"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0

# ---------------- GAME STATE ----------------

queue = []
duels = {}

# ---------------- QUIZ BANK (بزرگ شده) ----------------

quiz_bank = [
    ("پایتخت ایران؟", ["تهران", "مشهد", "شیراز", "تبریز"], "تهران"),
    ("2+2؟", ["3", "4", "5", "6"], "4"),
    ("5×5؟", ["20", "25", "30", "15"], "25"),
    ("پایتخت ترکیه؟", ["آنکارا", "استانبول", "ازمیر", "وان"], "آنکارا"),
    ("رنگ آسمان؟", ["آبی", "قرمز", "سبز", "زرد"], "آبی"),
    ("10-3؟", ["5", "6", "7", "8"], "7"),
    ("پایتخت فرانسه؟", ["پاریس", "لیون", "مارسی", "نیس"], "پاریس"),
    ("عدد اول کدام است؟", ["4", "6", "7", "9"], "7"),
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

# ---------------- KEYBOARD ----------------

def quiz_keyboard(options):
    return {
        "inline_keyboard": [
            [{"text": options[0], "callback_data": options[0]},
             {"text": options[1], "callback_data": options[1]}],
            [{"text": options[2], "callback_data": options[2]},
             {"text": options[3], "callback_data": options[3]}],
        ]
    }

# ---------------- MATCHMAKING ----------------

def matchmake(chat_id):

    queue.append(chat_id)

    if len(queue) < 2:
        send(chat_id, "⏳ منتظر حریف...")
        return None

    p1 = queue.pop(0)
    p2 = queue.pop(0)

    duel_id = str(random.randint(1000,9999))

    duels[duel_id] = {
        "p1": p1,
        "p2": p2,
        "score": {p1:0, p2:0},
        "round": 0,
        "current_q": None,
        "answered": False
    }

    send(p1, "⚔️ حریف پیدا شد! شروع شد!")
    send(p2, "⚔️ حریف پیدا شد! شروع شد!")

    start_round(duel_id)

    return duel_id

# ---------------- ROUND SYSTEM ----------------

def start_round(duel_id):

    d = duels.get(duel_id)
    if not d:
        return

    if d["round"] >= 10:
        end_game(duel_id)
        return

    d["round"] += 1
    d["answered"] = False

    q = random.choice(quiz_bank)
    d["current_q"] = q

    text = f"""
🧠 راند {d['round']}/10

❓ {q[0]}

⏳ 5 ثانیه وقت داری!
"""

    kb = quiz_keyboard(q[1])

    send(d["p1"], text, kb)
    send(d["p2"], text, kb)

    # تایمر 5 ثانیه
    threading.Timer(5, timeout_round, args=[duel_id]).start()

# ---------------- TIMEOUT ----------------

def timeout_round(duel_id):

    d = duels.get(duel_id)
    if not d:
        return

    start_round(duel_id)

# ---------------- END GAME ----------------

def end_game(duel_id):

    d = duels[duel_id]

    p1, p2 = d["p1"], d["p2"]

    s1 = d["score"][p1]
    s2 = d["score"][p2]

    if s1 > s2:
        res = f"🏆 بازیکن 1 برد!\n{p1}"
    elif s2 > s1:
        res = f"🏆 بازیکن 2 برد!\n{p2}"
    else:
        res = "🤝 مساوی شدید!"

    send(p1, f"🎮 پایان بازی\n{s1} - {s2}\n{res}")
    send(p2, f"🎮 پایان بازی\n{s1} - {s2}\n{res}")

    del duels[duel_id]

# ---------------- BOT LOOP ----------------

print("🚀 QUIZ DUEL STARTED")

while True:

    try:

        res = requests.post(
            f"{BASE_URL}/getUpdates",
            json={"offset": offset},
            timeout=15
        ).json()

        for u in res.get("result", []):

            offset = u["update_id"] + 1

            # ---------------- MESSAGE ----------------

            if "message" in u:

                msg = u["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text","")

                if text == "/start":
                    send(chat_id, "🎮 برای شروع دوئل بنویس: بازی")

                elif text == "بازی":
                    matchmake(chat_id)

            # ---------------- CALLBACK ----------------

            if "callback_query" in u:

                cb = u["callback_query"]
                data = cb["data"]
                chat_id = cb["message"]["chat"]["id"]

                # پیدا کردن دوئل
                for duel_id, d in duels.items():

                    if chat_id not in [d["p1"], d["p2"]]:
                        continue

                    if d["answered"]:
                        continue

                    correct = d["current_q"][2]

                    if data == correct:

                        d["score"][chat_id] += 1
                        d["answered"] = True

                        send(chat_id, "✅ درست!")

                        enemy = d["p1"] if chat_id == d["p2"] else d["p2"]
                        send(enemy, "❌ حریف جواب درست داد!")

                        start_round(duel_id)

                    else:
                        send(chat_id, "❌ غلط!")

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
