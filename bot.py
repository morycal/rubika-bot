import requests
import time
import random
from datetime import datetime

TOKEN = "1597508244:uHdj4lnrEAz6lENe0GQI6cUltRiW3ogrNeY"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0

# ---------------- DATA ----------------

games = {}
xp = {}
rpg = {}
duels = {}

# ---------------- FUN ----------------

greetings = ["سلام 😄", "هلو 👋", "سلام رفیق 😎"]
jokes = ["😂 باگ‌ها همیشه برمی‌گردن", "🤣 من فقط یه باتم!"]
rps_choices = ["سنگ", "کاغذ", "قیچی"]

# ---------------- SEND ----------------

def send_message(chat_id, text, reply_to=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_to:
        payload["reply_to_message_id"] = reply_to

    try:
        requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
    except:
        pass

print("🚀 FULL ULTIMATE BOT STARTED")

# ---------------- LOOP ----------------

while True:

    try:
        res = requests.post(
            f"{BASE_URL}/getUpdates",
            json={"offset": offset},
            timeout=15
        )

        data = res.json()
        updates = data.get("result", [])

        for update in updates:

            offset = update["update_id"] + 1

            msg = update.get("message")
            if not msg:
                continue

            chat_id = msg["chat"]["id"]
            text = msg.get("text", "").lower()
            message_id = msg.get("message_id")

            print("USER:", text)

            # ---------------- START ----------------

            if text == "/start":
                send_message(chat_id,
                    "🤖 سلام!\n"
                    "من بات بازی‌دار هستم 😎\n\n"
                    "🎮 rps → سنگ کاغذ قیچی\n"
                    "🧠 quiz → سوال\n"
                    "🤖 ai → سوال هوشمند\n"
                    "🎮 rpg → بازی نقش‌آفرینی\n"
                    "🤼 دوئل → دوئل آنلاین\n"
                    "🏆 leaderboard → امتیاز",
                    reply_to=message_id
                )

            # ---------------- CHAT ----------------

            elif "سلام" in text:
                send_message(chat_id, random.choice(greetings), reply_to=message_id)

            elif text == "جک":
                send_message(chat_id, random.choice(jokes), reply_to=message_id)

            elif text == "زمان":
                send_message(chat_id, str(datetime.now()), reply_to=message_id)

            # ---------------- RPS ----------------

            elif text == "rps":
                games[chat_id] = {"type": "rps"}
                send_message(chat_id, "✊ سنگ / کاغذ / قیچی؟", reply_to=message_id)

            elif chat_id in games and games[chat_id]["type"] == "rps":

                bot = random.choice(rps_choices)

                if text == bot:
                    result = "مساوی 😐"
                elif (text == "سنگ" and bot == "قیچی") or \
                     (text == "کاغذ" and bot == "سنگ") or \
                     (text == "قیچی" and bot == "کاغذ"):
                    result = "تو بردی 🎉"
                    xp[chat_id] = xp.get(chat_id, 0) + 2
                else:
                    result = "من بردم 😎"

                send_message(chat_id, f"🤖 من: {bot}\n📊 {result}", reply_to=message_id)
                games.pop(chat_id, None)

            # ---------------- QUIZ ----------------

            elif text == "quiz":
                q = random.choice([
                    ("2+2؟", "4"),
                    ("پایتخت ایران؟", "تهران"),
                    ("آب یخ چند درجه؟", "0")
                ])

                games[chat_id] = {"type": "quiz", "ans": q[1]}
                send_message(chat_id, q[0], reply_to=message_id)

            elif chat_id in games and games[chat_id]["type"] == "quiz":

                if text == games[chat_id]["ans"]:
                    xp[chat_id] = xp.get(chat_id, 0) + 3
                    send_message(chat_id, "🎉 درست!", reply_to=message_id)
                else:
                    send_message(chat_id, f"❌ غلط! جواب: {games[chat_id]['ans']}", reply_to=message_id)

                games.pop(chat_id, None)

            # ---------------- AI ----------------

            elif text == "ai":

                q = random.choice([
                    ("3+5؟", "8"),
                    ("پایتخت ترکیه؟", "آنکارا"),
                    ("5×2؟", "10")
                ])

                games[chat_id] = {"type": "ai", "ans": q[1]}
                send_message(chat_id, f"🤖 AI سوال:\n{q[0]}", reply_to=message_id)

            elif chat_id in games and games[chat_id]["type"] == "ai":

                if text == games[chat_id]["ans"]:
                    xp[chat_id] = xp.get(chat_id, 0) + 5
                    send_message(chat_id, "🤖 درست!", reply_to=message_id)
                else:
                    send_message(chat_id, f"❌ غلط! جواب: {games[chat_id]['ans']}", reply_to=message_id)

                games.pop(chat_id, None)

            # ---------------- RPG ----------------

            elif text == "rpg":
                rpg[chat_id] = {"hp": 100, "gold": 0}
                send_message(chat_id,
                    "🎮 RPG شروع شد!\nنبرد / گنج / استراحت",
                    reply_to=message_id
                )

            elif text == "نبرد" and chat_id in rpg:

                dmg = random.randint(5, 20)
                rpg[chat_id]["hp"] -= dmg
                xp[chat_id] = xp.get(chat_id, 0) + 2

                send_message(chat_id,
                    f"⚔️ دمیج: {dmg}\n❤️ HP: {rpg[chat_id]['hp']}",
                    reply_to=message_id
                )

                if rpg[chat_id]["hp"] <= 0:
                    send_message(chat_id, "☠️ باختی!")
                    del rpg[chat_id]

            elif text == "گنج" and chat_id in rpg:

                gold = random.randint(10, 50)
                rpg[chat_id]["gold"] += gold

                send_message(chat_id, f"💰 {gold} سکه گرفتی!", reply_to=message_id)

            elif text == "استراحت" and chat_id in rpg:

                heal = random.randint(10, 30)
                rpg[chat_id]["hp"] += heal

                send_message(chat_id, f"😴 +{heal} HP", reply_to=message_id)

            # ---------------- DUEL ----------------

            elif text.startswith("دوئل"):

                duels[chat_id] = {"hp1": 50, "hp2": 50}

                send_message(chat_id,
                    "🤼 دوئل شروع شد!\nبزن: حمله",
                    reply_to=message_id
                )

            elif text == "حمله" and chat_id in duels:

                dmg = random.randint(5, 15)
                duels[chat_id]["hp2"] -= dmg

                send_message(chat_id,
                    f"⚔️ دمیج: {dmg}\nHP دشمن: {duels[chat_id]['hp2']}",
                    reply_to=message_id
                )

                if duels[chat_id]["hp2"] <= 0:
                    send_message(chat_id, "🏆 بردی دوئل!")
                    xp[chat_id] = xp.get(chat_id, 0) + 10
                    del duels[chat_id]

            # ---------------- LEADERBOARD ----------------

            elif text == "leaderboard":

                board = sorted(xp.items(), key=lambda x: x[1], reverse=True)[:5]

                msg = "🏆 لیدربورد:\n\n"

                for i, (u, s) in enumerate(board, 1):
                    msg += f"{i}. {u} → {s} XP\n"

                send_message(chat_id, msg, reply_to=message_id)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
