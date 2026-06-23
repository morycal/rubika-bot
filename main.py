import os
import time
import sqlite3
import requests
from openai import OpenAI

# ================= CONFIG =================
BALE_TOKEN = os.getenv("BALE_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "586110315"))

BASE_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

CARD = "1010202030304040"

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

# ================= DB =================
db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
questions INTEGER DEFAULT 0,
vip_until INTEGER DEFAULT 0,
last_message INTEGER DEFAULT 0,
banned INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS history(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
role TEXT,
message TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS payments(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
plan TEXT,
tracking TEXT,
status INTEGER DEFAULT 0
)
""")

db.commit()

# ================= SEND =================
def send(chat_id, text, reply_markup=None):
    data = {
        "chat_id": chat_id,
        "text": text[:4000],
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = reply_markup

    requests.post(f"{BASE_URL}/sendMessage", json=data, timeout=20)

# ================= USER =================
def get_user(uid):
    cur.execute("SELECT questions,vip_until,last_message,banned FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO users(user_id) VALUES(?)", (uid,))
        db.commit()
        return (0, 0, 0, 0)
    return row

def update_last(uid, now):
    cur.execute("UPDATE users SET last_message=? WHERE user_id=?", (now, uid))
    db.commit()

def add_history(uid, role, msg):
    cur.execute(
        "INSERT INTO history(user_id,role,message) VALUES(?,?,?)",
        (uid, role, msg[:2000])
    )
    db.commit()

# ================= AI =================
def ask_ai(uid, text):
    msgs = [{"role": "system", "content": "تو یک دستیار فارسی حرفه‌ای هستی."}]

    cur.execute("""
        SELECT role,message FROM history
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 8
    """, (uid,))

    rows = cur.fetchall()[::-1]

    for r, m in rows:
        msgs.append({"role": r, "content": m})

    msgs.append({"role": "user", "content": text})

    res = client.chat.completions.create(
        model="Qwen/Qwen3-8B",
        messages=msgs,
        max_tokens=300
    )

    return res.choices[0].message.content

# ================= VIP MENU =================
def vip_menu(chat_id):
    send(chat_id, "💎 انتخاب پلن VIP:",
         reply_markup={
             "inline_keyboard": [
                 [{"text": "📅 روزانه - 10k", "callback_data": "vip_1"}],
                 [{"text": "📆 هفتگی - 50k", "callback_data": "vip_7"}],
                 [{"text": "🗓 ماهانه - 150k", "callback_data": "vip_30"}],
                 [{"text": "💎 سالانه - 1M", "callback_data": "vip_365"}],
             ]
         })

# ================= MAIN =================
print("BOT STARTED")
offset = 0

while True:
    try:
        data = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": offset, "timeout": 30},
            timeout=35
        ).json()

        for upd in data.get("result", []):

            offset = upd["update_id"] + 1

            # ================= CALLBACKS =================
            if "callback_query" in upd:
                cq = upd["callback_query"]
                data_cb = cq["data"]
                uid = cq["from"]["id"]
                chat_id = cq["message"]["chat"]["id"]

                # ========== VIP ==========
                plans = {
                    "vip_1": (1, 10000),
                    "vip_7": (7, 50000),
                    "vip_30": (30, 150000),
                    "vip_365": (365, 1000000),
                }

                if data_cb in plans:
                    days, price = plans[data_cb]

                    send(chat_id,
                         f"💳 پرداخت:\n"
                         f"💰 مبلغ: {price}\n"
                         f"💳 کارت:\n{CARD}\n\n"
                         f"📌 بعد از پرداخت:\n"
                         f"پرداخت {days}d کدپیگیری")

                    continue

                # ========== ADMIN PANEL ==========
                if uid == ADMIN_ID:

                    if data_cb == "admin_payments":

                        cur.execute("""
                            SELECT id,user_id,plan,tracking
                            FROM payments
                            WHERE status=0
                            ORDER BY id DESC
                            LIMIT 10
                        """)
                        rows = cur.fetchall()

                        buttons = []

                        text = "💳 پرداخت‌های در انتظار:\n\n"

                        for i,u,p,t in rows:
                            text += f"{i} | {u} | {p} | {t}\n"
                            buttons.append([
                                {"text": f"✅ تایید {i}", "callback_data": f"ap_{i}"}
                            ])

                        send(chat_id, text if rows else "خالی",
                             reply_markup={"inline_keyboard": buttons})
                        continue

                    if data_cb == "admin_stats":

                        cur.execute("SELECT COUNT(*) FROM users")
                        users = cur.fetchone()[0]

                        cur.execute("SELECT COUNT(*) FROM payments WHERE status=0")
                        pend = cur.fetchone()[0]

                        send(chat_id,
                             f"📊 آمار:\n👥 {users}\n💳 {pend}")
                        continue

                    if data_cb.startswith("ap_"):

                        pid = int(data_cb.split("_")[1])

                        cur.execute("UPDATE payments SET status=1 WHERE id=?", (pid,))
                        db.commit()

                        send(chat_id, f"✅ تایید شد: {pid}")
                        continue

                continue

            # ================= MESSAGE =================
            if "message" not in upd:
                continue

            msg = upd["message"]
            uid = msg["from"]["id"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "").strip()

            if not text:
                continue

            q, vip_until, last, banned = get_user(uid)

            if banned:
                send(chat_id, "⛔ شما بن هستید")
                continue

            now = int(time.time())

            if uid != ADMIN_ID and now - last < 3:
                send(chat_id, "⏳ اسپم نکن")
                continue

            update_last(uid, now)

            cmd = text.split("@")[0].strip()

            # ================= START =================
            if cmd == "/start":
                send(chat_id,
                     "👋 سلام\n"
                     "🤖 ربات AI فعال است\n"
                     "💎 خرید VIP: خرید vip")
                continue

            # ================= VIP =================
            if text.lower() == "خرید vip":
                vip_menu(chat_id)
                continue

            # ================= ADMIN =================
            if cmd == "/admin" and uid == ADMIN_ID:
                send(chat_id,
                     "⚙️ پنل ادمین",
                     reply_markup={
                         "inline_keyboard": [
                             [{"text": "💳 پرداخت‌ها", "callback_data": "admin_payments"}],
                             [{"text": "📊 آمار", "callback_data": "admin_stats"}]
                         ]
                     })
                continue

            # ================= PAY MANUAL =================
            if text.startswith("پرداخت "):
                parts = text.split(maxsplit=2)

                if len(parts) < 3:
                    send(chat_id, "فرمت: پرداخت ماهانه 123")
                    continue

                plan = parts[1]
                track = parts[2]

                cur.execute("""
                    INSERT INTO payments(user_id,plan,tracking)
                    VALUES(?,?,?)
                """, (uid, plan, track))
                db.commit()

                send(chat_id, "✅ ثبت شد")
                send(ADMIN_ID, f"💳 پرداخت\n{uid}\n{plan}\n{track}")
                continue

            # ================= VIP LIMIT =================
            is_vip = vip_until > now

            if not is_vip and q >= 5:
                send(chat_id, "🚫 محدود شدی، VIP بخر")
                continue

            # ================= AI =================
            try:
                answer = ask_ai(uid, text)

                add_history(uid, "user", text)
                add_history(uid, "assistant", answer)

                if not is_vip:
                    cur.execute(
                        "UPDATE users SET questions=questions+1 WHERE user_id=?",
                        (uid,)
                    )
                    db.commit()

                send(chat_id, answer)

            except Exception as e:
                send(chat_id, "❌ خطای AI")

    except Exception as e:
        print("ERR:", e)
        time.sleep(3)
