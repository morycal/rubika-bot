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

# ================= DATABASE =================
db = sqlite3.connect("users.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    questions INTEGER DEFAULT 0,
    vip_until INTEGER DEFAULT 0,
    banned INTEGER DEFAULT 0,
    last_message INTEGER DEFAULT 0
)
""")
db.commit()


# ================= TELEGRAM =================
def send(chat_id, text):
    requests.post(
        f"{BASE_URL}/sendMessage",
        json={"chat_id": chat_id, "text": text[:4000]},
        timeout=30
    )


# ================= USER =================
def get_user(user_id):
    cur.execute("SELECT questions,vip_until,banned,last_message FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()

    if not row:
        cur.execute(
            "INSERT INTO users(user_id,questions,vip_until,banned,last_message) VALUES(?,?,?,?,?)",
            (user_id, 0, 0, 0, 0)
        )
        db.commit()
        return (0, 0, 0, 0)

    return row


def update_last(user_id):
    cur.execute("UPDATE users SET last_message=? WHERE user_id=?", (int(time.time()), user_id))
    db.commit()


def add_question(user_id):
    cur.execute("UPDATE users SET questions = questions + 1 WHERE user_id=?", (user_id,))
    db.commit()


def set_vip(user_id, days):
    now = int(time.time())

    if days == -1:
        vip_until = 10**12
    else:
        _, vip_until, _, _ = get_user(user_id)
        base = max(vip_until, now)
        vip_until = base + (days * 86400)

    cur.execute("UPDATE users SET vip_until=? WHERE user_id=?", (vip_until, user_id))
    db.commit()


def remove_vip(user_id):
    cur.execute("UPDATE users SET vip_until=0 WHERE user_id=?", (user_id,))
    db.commit()


def ban(user_id):
    cur.execute("UPDATE users SET banned=1 WHERE user_id=?", (user_id,))
    db.commit()


def unban(user_id):
    cur.execute("UPDATE users SET banned=0 WHERE user_id=?", (user_id,))
    db.commit()


def can_use(user_id):
    q, vip, banned, last = get_user(user_id)

    if banned == 1:
        return False

    if vip > int(time.time()):
        return True

    return q < 3


# ================= AI =================
def ask_ai(text):
    try:
        res = client.chat.completions.create(
            model="Qwen/Qwen3-8B",
            messages=[
                {"role": "system", "content": "تو یک دستیار فارسی حرفه‌ای هستی."},
                {"role": "user", "content": text}
            ],
            max_tokens=500
        )
        return res.choices[0].message.content

    except Exception as e:
        return f"خطا AI: {e}"


# ================= BOT LOOP =================
offset = 0
print("BOT STARTED")

while True:
    try:
        updates = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": offset, "timeout": 30},
            timeout=35
        ).json()

        for upd in updates.get("result", []):
            offset = upd["update_id"] + 1

            if "message" not in upd:
                continue

            msg = upd["message"]

            chat_id = msg["chat"]["id"]
            user_id = msg["from"]["id"]
            text = msg.get("text", "").strip()

            if not text:
                continue

            q, vip, banned, last = get_user(user_id)

            # ================= SPAM PROTECTION =================
            now = int(time.time())
            if now - last < 5:
                send(chat_id, "⏳ لطفاً کمی صبر کنید")
                continue

            update_last(user_id)

            # ================= BAN CHECK =================
            if banned == 1:
                send(chat_id, "⛔ شما بن هستید")
                continue

            # ================= START =================
            if text == "/start":
                send(chat_id,
                    f"سلام 👋\n"
                    f"۳ سوال رایگان داری\n"
                    f"ادمین: @ahmmad24"
                )
                continue

            # ================= STATUS =================
            if text == "/status":
                if vip > now:
                    send(chat_id, "⭐ VIP فعال است")
                else:
                    send(chat_id, f"سوال باقی‌مانده: {max(0, 3-q)}")
                continue

            # ================= ADMIN CHECK =================
            is_admin = (user_id == ADMIN_ID)

            # ================= VIP =================
            if is_admin and text.startswith("/vip"):
                parts = text.split()

                if len(parts) < 3:
                    send(chat_id, "مثال: /vip 123 30")
                    continue

                target = int(parts[1])
                days = int(parts[2])

                set_vip(target, days)

                send(chat_id, f"VIP فعال شد برای {target}")

                continue

            # ================= UNVIP =================
            if is_admin and text.startswith("/unvip"):
                target = int(text.split()[1])
                remove_vip(target)
                send(chat_id, "VIP حذف شد")
                continue

            # ================= BAN =================
            if is_admin and text.startswith("/ban"):
                target = int(text.split()[1])
                ban(target)
                send(chat_id, "بن شد")
                continue

            # ================= UNBAN =================
            if is_admin and text.startswith("/unban"):
                target = int(text.split()[1])
                unban(target)
                send(chat_id, "آنبن شد")
                continue

            # ================= STATS =================
            if is_admin and text == "/stats":
                cur.execute("SELECT COUNT(*) FROM users")
                users = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM users WHERE vip_until>?", (now,))
                vipc = cur.fetchone()[0]

                send(chat_id,
                    f"👥 کاربران: {users}\n⭐ VIP: {vipc}"
                )
                continue

            # ================= BROADCAST =================
            if is_admin and text.startswith("/broadcast"):
                msg_text = text.replace("/broadcast", "").strip()

                cur.execute("SELECT user_id FROM users")
                for (uid,) in cur.fetchall():
                    send(uid, msg_text)

                continue

            # ================= ACCESS CHECK =================
            if not can_use(user_id):
                send(chat_id,
                    f"❌ اتمام اعتبار\n"
                    f"با ادمین هماهنگ کنید\nID: @ahmmad24"
                )
                continue

            # ================= USAGE COUNT =================
            if vip < now:
                add_question(user_id)

            # ================= AI =================
            answer = ask_ai(text)
            send(chat_id, answer)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)
