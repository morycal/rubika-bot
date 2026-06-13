import requests
import time
import random
from datetime import datetime

TOKEN = "1597508244:uHdj4lnrEAz6lENe0GQI6cUltRiW3ogrNeY"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0

# ---------------- MMO DATA ----------------

players = {}
queue = []
duels = {}
guilds = {}
boss = {"hp": 500}

# ---------------- PLAYER ----------------

def get_player(uid):
    if uid not in players:
        players[uid] = {
            "xp": 0,
            "gold": 100,
            "inventory": [],
            "guild": None
        }
    return players[uid]

# ---------------- SEND ----------------

def send(chat_id, text, reply_to=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_to:
        payload["reply_to_message_id"] = reply_to

    try:
        requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
    except:
        pass

print("🚀 MMO BOT STARTED")

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

        for u in updates:

            offset = u["update_id"] + 1

            msg = u.get("message")
            if not msg:
                continue

            chat_id = msg["chat"]["id"]
            text = msg.get("text", "").lower()
            mid = msg.get("message_id")

            player = get_player(chat_id)

            print("USER:", text)

            # ---------------- START ----------------

            if text == "/start":
                send(chat_id,
                    "🎮 MMO BOT فعال شد!\n\n"
                    "دوئل → PvP\n"
                    "حمله → در PvP\n"
                    "باس → حمله به باس جهانی\n"
                    "کلن اسم → ساخت کلن\n"
                    "کلن join اسم → ورود\n"
                    "loot → آیتم\n"
                    "inventory → وسایل\n"
                    "پروفایل → مشخصات\n"
                    "لیدربورد → رتبه‌ها",
                    mid
                )

            # ---------------- MATCHMAKING ----------------

            elif text == "دوئل":

                if chat_id in queue:
                    send(chat_id, "⏳ هنوز تو صفی...", mid)
                else:
                    queue.append(chat_id)
                    send(chat_id, "⏳ وارد صف شدی...", mid)

                if len(queue) >= 2:

                    p1 = queue.pop(0)
                    p2 = queue.pop(0)

                    duel_id = str(random.randint(1000, 9999))

                    duels[duel_id] = {
                        "p1": p1,
                        "p2": p2,
                        "turn": p1,
                        "hp": {p1: 100, p2: 100}
                    }

                    send(p1, "⚔️ حریف پیدا شد! تو شروع کن", None)
                    send(p2, "⚔️ حریف پیدا شد! صبر کن نوبتت بشه", None)

            # ---------------- ATTACK ----------------

            elif text == "حمله":

                duel_id = None

                for d, v in duels.items():
                    if chat_id in [v["p1"], v["p2"]]:
                        duel_id = d
                        duel = v
                        break

                if not duel_id:
                    send(chat_id, "❌ داخل دوئل نیستی", mid)
                    continue

                if duel["turn"] != chat_id:
                    send(chat_id, "⏳ نوبت تو نیست", mid)
                    continue

                dmg = random.randint(10, 30)

                enemy = duel["p2"] if chat_id == duel["p1"] else duel["p1"]

                duel["hp"][enemy] -= dmg

                player["xp"] += 5
                player["gold"] += 10

                send(chat_id, f"⚔️ دمیج: {dmg}", mid)
                send(enemy, f"💥 خوردی: {dmg}", None)

                if duel["hp"][enemy] <= 0:

                    send(chat_id, "🏆 بردی!", mid)
                    send(enemy, "💀 باختی!", None)

                    player["xp"] += 20
                    player["gold"] += 50

                    del duels[duel_id]

                else:
                    duel["turn"] = enemy

            # ---------------- BOSS ----------------

            elif text == "باس":

                dmg = random.randint(5, 25)
                boss["hp"] -= dmg

                player["xp"] += 10
                player["gold"] += 15

                send(chat_id,
                    f"🔥 حمله کردی!\n💥 دمیج: {dmg}\n❤️ HP باس: {boss['hp']}",
                    mid
                )

                if boss["hp"] <= 0:
                    send(chat_id, "👑 باس شکست خورد!")
                    boss["hp"] = 500

            # ---------------- GUILD ----------------

            elif text.startswith("کلن "):

                parts = text.split()

                if len(parts) == 2:

                    name = parts[1]

                    guilds[name] = {
                        "members": [chat_id]
                    }

                    player["guild"] = name

                    send(chat_id, f"🏰 کلن {name} ساخته شد!", mid)

                elif len(parts) == 3 and parts[1] == "join":

                    name = parts[2]

                    if name in guilds:
                        guilds[name]["members"].append(chat_id)
                        player["guild"] = name
                        send(chat_id, f"✅ وارد کلن {name} شدی!", mid)

            # ---------------- INVENTORY ----------------

            elif text == "loot":

                item = random.choice(["شمشیر", "زره", "معجون", "سنگ جادویی"])

                player["inventory"].append(item)

                send(chat_id, f"🎁 گرفتی: {item}", mid)

            elif text == "inventory":

                send(chat_id,
                    f"🎒 آیتم‌ها: {player['inventory']}\n💰 Gold: {player['gold']}",
                    mid
                )

            # ---------------- PROFILE ----------------

            elif text == "پروفایل":

                level = player["xp"] // 50

                send(chat_id,
                    f"""
👤 پروفایل
⭐ Level: {level}
💰 Gold: {player['gold']}
🏰 Guild: {player['guild']}
🎒 Items: {len(player['inventory'])}
""",
                    mid
                )

            # ---------------- LEADERBOARD ----------------

            elif text == "لیدربورد":

                board = sorted(players.items(), key=lambda x: x[1]["xp"], reverse=True)[:10]

                msg = "🏆 لیدربورد:\n\n"

                for i, (uid, p) in enumerate(board, 1):
                    msg += f"{i}. {uid} → {p['xp']} XP\n"

                send(chat_id, msg, mid)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
