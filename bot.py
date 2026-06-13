import requests
import time
from datetime import datetime
import random

TOKEN = "1597508244:uHdj4lnrEAz6lENe0GQI6cUltRiW3ogrNeY"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0


# ---------------- DATA ----------------

games = {}
xp = {}


# ---------------- FUN TEXT ----------------

greetings = [
    "سلام 😄 خوش اومدی!",
    "هلووو 👋",
    "سلام رفیق 😎",
    "سلام! چه خبر؟"
]

how_are_you = [
    "خوبم مرسی 🙂 تو چطوری؟",
    "عالی‌ام 😄",
    "رو به راهم 👌",
    "زنده‌ام 😆"
]

chitchat = [
    "دارم با تو چت می‌کنم 😄",
    "منتظر پیام توام 😎",
    "دارم فکر می‌کنم چرا باگ داریم 😂",
]

goodbye = [
    "فعلاً 👋",
    "بای بای 😎",
    "خدافظ ❤️",
]

jokes = [
    "😂 چرا برنامه‌نویسا قهوه می‌خورن؟ چون باگ‌ها بیدارن 😆",
    "🤣 1٪ کد، 99٪ چرا کار نکرد؟",
    "😆 من یه باگ بودم، الان آپدیت شدم 😎",
]

rps_choices = ["سنگ", "کاغذ", "قیچی"]


# ---------------- SEND ----------------

def send_message(chat_id, text, reply_to=None):
    try:
        payload = {
            "chat_id": chat_id,
            "text": text
        }

        if reply_to:
            payload["reply_to_message_id"] = reply_to

        requests.post(
            f"{BASE_URL}/sendMessage",
            json=payload,
            timeout=10
        )

    except Exception as e:
        print("SEND ERROR:", e)


print("🚀 FULL GAME BOT STARTED")


# ---------------- LOOP ----------------

while True:

    try:
        res = requests.post(
            f"{BASE_URL}/getUpdates",
            json={"offset": offset},
            timeout=15
        )

        data = res.json()

        if not data.get("ok"):
            time.sleep(1)
            continue

        updates = data.get("result", [])

        for update in updates:

            offset = update["update_id"] + 1

            message = update.get("message")
            if not message:
                continue

            chat_id = message["chat"]["id"]
            text = message.get("text", "").lower()
            message_id = message.get("message_id")

            print("USER:", text)

            # ---------------- START ----------------

            if text == "/start":
                send_message(chat_id,
                    "احمد خوابه به خودم بگو بهش میگم\n",
                    reply_to=message_id
                )

            # ---------------- CHAT ----------------

            elif "سلام" in text:
                send_message(chat_id, random.choice(greetings), reply_to=message_id)

            elif "خوبی" in text:
                send_message(chat_id, random.choice(how_are_you), reply_to=message_id)

            elif "چیکار" in text:
                send_message(chat_id, random.choice(chitchat), reply_to=message_id)

            elif "بای" in text:
                send_message(chat_id, random.choice(goodbye), reply_to=message_id)

            elif text == "joke":
                send_message(chat_id, random.choice(jokes), reply_to=message_id)

            elif text == "time":
                now = datetime.now().strftime("%Y-%m-%d ⏰ %H:%M:%S")
                send_message(chat_id, f"⏰ {now}", reply_to=message_id)


            # ---------------- RPS GAME ----------------

            elif text == "بازی rps":
                games[chat_id] = {"type": "rps"}

                send_message(chat_id,
                    "✊ بازی شروع شد!\n"
                    "یکی بفرست: سنگ / کاغذ / قیچی",
                    reply_to=message_id
                )

            elif chat_id in games and games[chat_id].get("type") == "rps":

                bot = random.choice(rps_choices)

                if text not in rps_choices:
                    send_message(chat_id, "فقط سنگ / کاغذ / قیچی 😄", reply_to=message_id)
                else:

                    if text == bot:
                        result = "مساوی 😐"
                    elif (text == "سنگ" and bot == "قیچی") or \
                         (text == "کاغذ" and bot == "سنگ") or \
                         (text == "قیچی" and bot == "کاغذ"):
                        result = "تو بردی 🎉"
                        xp[chat_id] = xp.get(chat_id, 0) + 2
                    else:
                        result = "من بردم 😎"

                    send_message(chat_id,
                        f"🤖 من: {bot}\n📊 {result}",
                        reply_to=message_id
                    )

                    games.pop(chat_id, None)


            # ---------------- QUIZ ----------------

            elif text == "quiz":

                q = random.choice([
                    ("پایتخت ایران؟", "تهران"),
                    ("2+2؟", "4"),
                    ("رنگ آسمان؟", "آبی")
                ])

                games[chat_id] = {"type": "quiz", "ans": q[1]}

                send_message(chat_id, f"🧠 سوال:\n{q[0]}", reply_to=message_id)

            elif chat_id in games and games[chat_id].get("type") == "quiz":

                if text == games[chat_id]["ans"]:
                    xp[chat_id] = xp.get(chat_id, 0) + 3
                    send_message(chat_id, "🎉 درست! +3 XP 😎", reply_to=message_id)
                else:
                    send_message(chat_id,
                        f"❌ غلط!\nجواب: {games[chat_id]['ans']}",
                        reply_to=message_id
                    )

                games.pop(chat_id, None)


            # ---------------- LEVEL ----------------

            elif text == "level":
                user_xp = xp.get(chat_id, 0)
                level = user_xp // 10

                send_message(chat_id,
                    f"🔥 Level: {level}\n⭐ XP: {user_xp}",
                    reply_to=message_id
                )


            # ---------------- LEADERBOARD ----------------

            elif text == "leaderboard":

                board = sorted(xp.items(), key=lambda x: x[1], reverse=True)[:5]

                msg = "🏆 لیدربورد:\n\n"

                for i, (u, score) in enumerate(board, 1):
                    msg += f"{i}. کاربر {u} → {score} XP\n"

                send_message(chat_id, msg, reply_to=message_id)


            # ---------------- UNKNOWN ----------------

            else:
                send_message(chat_id,
                    "😅 نفهمیدم چی گفتی\nیه /start بزن 😎",
                    reply_to=message_id
                )

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
