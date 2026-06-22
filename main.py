import os
import time
import requests
import psycopg2
from openai import OpenAI

# ================= CONFIG =================
BALE_TOKEN = os.getenv("BALE_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

ADMIN_ID = 586110315

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

BASE_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# ================= DB =================
cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id BIGINT PRIMARY KEY,
    questions INT DEFAULT 0,
    vip_until BIGINT DEFAULT 0,
    banned INT DEFAULT 0,
    last_message BIGINT DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS memory(
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    role TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
)
""")
conn.commit()

# ================= BOT =================
def send(chat_id, text):
    requests.post(
        f"{BASE_URL}/sendMessage",
        json={"chat_id": chat_id, "text": text[:4000]},
        timeout=30
    )


def get_user(user_id):
    cur.execute("SELECT questions,vip_until,banned,last_message FROM users WHERE user_id=%s", (user_id,))
    row = cur.fetchone()

    if not row:
        cur.execute(
            "INSERT INTO users(user_id,questions,vip_until,banned,last_message) VALUES(%s,0,0,0,0)",
            (user_id,)
        )
        conn.commit()
        return (0, 0, 0, 0)

    return row


def update_last(user_id):
    cur.execute("UPDATE users SET last_message=%s WHERE user_id=%s", (int(time.time()), user_id))
    conn.commit()


def add_question(user_id):
    cur.execute("UPDATE users SET questions = questions + 1 WHERE user_id=%s", (user_id,))
    conn.commit()


def set_vip(user_id, days):
    now = int(time.time())

    get_user(user_id)

    cur.execute(
        "SELECT vip_until FROM users WHERE user_id=%s",
        (user_id,)
    )

    vip = cur.fetchone()[0]

    base = max(vip, now)
    new_vip = base + days * 86400

    cur.execute(
        "UPDATE users SET vip_until=%s WHERE user_id=%s",
        (new_vip, user_id)
    )

    conn.commit()


def remove_vip(user_id):
    cur.execute("UPDATE users SET vip_until=0 WHERE user_id=%s", (user_id,))
    conn.commit()


def ban(user_id):
    cur.execute("UPDATE users SET banned=1 WHERE user_id=%s", (user_id,))
    conn.commit()


def unban(user_id):
    cur.execute("UPDATE users SET banned=0 WHERE user_id=%s", (user_id,))
    conn.commit()


def can_use(user_id):
    q, vip, banned, last = get_user(user_id)

    if banned:
        return False

    if vip > int(time.time()):
        return True

    return q < 3


# ================= AI =================
def ask_ai(user_id, text):

   cur.execute(
    """
    SELECT role, content
    FROM memory
    WHERE user_id=%s
    ORDER BY id DESC
    LIMIT 10
    """,
    (user_id,)
)

    history = cur.fetchall()[::-1]

    messages = [
        {"role": "system", "content": "تو یک دستیار فارسی حرفه‌ای هستی."}
    ]

    for role, content in history:
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": text})

    res = client.chat.completions.create(
        model="Qwen/Qwen3-8B",
        messages=messages,
        max_tokens=500
    )

    answer = res.choices[0].message.content

    cur.execute(
        "INSERT INTO memory(user_id,role,content) VALUES(%s,%s,%s)",
        (user_id, "user", text)
    )

    cur.execute(
        "INSERT INTO memory(user_id,role,content) VALUES(%s,%s,%s)",
        (user_id, "assistant", answer)
    )

    conn.commit()

    return answer


# ================= LOOP =================
offset = 0
print("BOT STARTED")

while True:
    try:
        updates = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": offset, "timeout": 30},
            timeout=35
        ).json()

        for u in updates.get("result", []):
            offset = u["update_id"] + 1

            if "message" not in u:
                continue

            msg = u["message"]

            chat_id = msg["chat"]["id"]
            user_id = msg["from"]["id"]
            text = msg.get("text", "").strip()

            if not text:
                continue

            q, vip, banned, last = get_user(user_id)

            # anti spam
            now = int(time.time())
            if now - last < 4:
                send(chat_id, "⏳ صبر کن")
                continue

            update_last(user_id)

            if banned:
                send(chat_id, "⛔ بن هستی")
                continue

            # commands
            if text == "/start":
                send(chat_id, "سلام 👋")
                continue

            if text == "/reset":
                cur.execute("DELETE FROM memory WHERE user_id=%s", (user_id,))
                conn.commit()
                send(chat_id, "🧠 حافظه پاک شد")
                continue

            if text == "/status":
                if vip > now:
                    send(chat_id, "⭐ VIP فعال")
                else:
                    send(chat_id, f"سوال باقی: {max(0, 3-q)}")
                continue

            # admin
            if user_id == ADMIN_ID:

                if text.startswith("/vip"):
                    _, uid, days = text.split()
                    set_vip(int(uid), int(days))
                    send(chat_id, "VIP OK")
                    continue

                if text.startswith("/unvip"):
                    uid = int(text.split()[1])
                    remove_vip(uid)
                    send(chat_id, "VIP OFF")
                    continue

                if text.startswith("/ban"):
                    uid = int(text.split()[1])
                    ban(uid)
                    send(chat_id, "BANNED")
                    continue

                if text.startswith("/unban"):
                    uid = int(text.split()[1])
                    unban(uid)
                    send(chat_id, "UNBANNED")
                    continue

            # limit
            if not can_use(user_id):
                send(chat_id, "❌ اتمام اعتبار")
                continue

            if vip < now:
                add_question(user_id)

            answer = ask_ai(user_id, text)
            send(chat_id, answer)

     except Exception as e:
        conn.rollback()
        print("ERR:", e)
        time.sleep(3)
