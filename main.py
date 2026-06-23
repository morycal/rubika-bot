# main.py
# Bale AI Bot - Railway Ready (Template)
# Configure environment variables:
# BALE_TOKEN, HF_TOKEN, ADMIN_ID

import os
import time
import sqlite3
import requests
from openai import OpenAI

BALE_TOKEN = os.getenv("BALE_TOKEN", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "586110315"))

CARD_NUMBER = "1010202030304040"
SUPPORT = "@ahmmad24"

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

BASE_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

db = sqlite3.connect("bot.db", check_same_thread=False)
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
tracking_code TEXT,
status INTEGER DEFAULT 0,
created_at INTEGER
)
""")

db.commit()

def send(chat_id, text):
    requests.post(
        f"{BASE_URL}/sendMessage",
        json={"chat_id": chat_id, "text": text[:4000]},
        timeout=30
    )

def get_user(uid):
    cur.execute("SELECT questions,vip_until,banned,last_message FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    if row:
        return row

    cur.execute(
        "INSERT INTO users(user_id) VALUES(?)",
        (uid,)
    )
    db.commit()
    return (0,0,0,0)

def add_history(uid, role, msg):
    cur.execute(
        "INSERT INTO history(user_id,role,message) VALUES(?,?,?)",
        (uid, role, msg[:3000])
    )
    db.commit()

def ask_ai(uid, text):
    msgs = [{"role":"system","content":"تو یک دستیار فارسی حرفه‌ای هستی."}]

    cur.execute("""
    SELECT role,message FROM history
    WHERE user_id=?
    ORDER BY id DESC
    LIMIT 10
    """,(uid,))

    rows = cur.fetchall()[::-1]

    for r,m in rows:
        msgs.append({"role":r,"content":m})

    msgs.append({"role":"user","content":text})

    res = client.chat.completions.create(
        model="Qwen/Qwen3-8B",
        messages=msgs,
        max_tokens=300
    )
    return res.choices[0].message.content

print("BOT STARTED")
offset = 0

while True:
    try:
        data = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset":offset,"timeout":30},
            timeout=35
        ).json()

        for upd in data.get("result", []):

            print(upd)

            offset = upd["update_id"] + 1

          if "message" not in upd:
             continue

            msg = upd["message"]
            uid = msg["from"]["id"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text","").strip()

            if not text:
                continue

            q,vip,banned,last = get_user(uid)

            if banned:
                send(chat_id,"⛔ شما مسدود هستید.")
                continue

            now = int(time.time())

            if uid != ADMIN_ID and now-last < 5:
                send(chat_id,"⏳ کمی صبر کنید.")
                continue

            cur.execute(
                "UPDATE users SET last_message=? WHERE user_id=?",
                (now, uid)
            )
            db.commit()

            if text == "/start":

    requests.post(
        f"{BASE_URL}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": "تست دکمه شیشه‌ای",
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {
                            "text": "تست",
                            "callback_data": "test"
                        }
                    ]
                ]
            }
        }
    )

    continue
            if text.lower() == "خرید vip":
                send(chat_id,
                f"""💎 پلن‌ها

روزانه: 10000
هفتگی: 50000
ماهانه: 150000
سه ماهه: 350000
شش ماهه: 600000
یک ساله: 1000000

کارت:
{CARD_NUMBER}

پس از پرداخت:
پرداخت <پلن> <کدپیگیری>
""")
                continue

            if text.startswith("پرداخت "):
                parts = text.split(maxsplit=2)

                if len(parts) < 3:
                    send(chat_id,"فرمت صحیح:\nپرداخت ماهانه 123456")
                    continue

                plan = parts[1]
                tracking = parts[2]

                cur.execute("""
                INSERT INTO payments(user_id,plan,tracking_code,created_at)
                VALUES(?,?,?,?)
                """,(uid,plan,tracking,now))
                db.commit()

                send(chat_id,"✅ درخواست ثبت شد و منتظر تایید ادمین است.")
                send(ADMIN_ID,f"درخواست پرداخت\nکاربر:{uid}\nپلن:{plan}\nکد:{tracking}")
                continue

            if uid == ADMIN_ID and text == "/panel":
                send(chat_id,
                "/stats\n/payments\n/approve payment_id days")
                continue

            if uid == ADMIN_ID and text == "/stats":
                cur.execute("SELECT COUNT(*) FROM users")
                users = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM payments WHERE status=0")
                pays = cur.fetchone()[0]

                send(chat_id,f"👥 Users:{users}\n💳 Pending:{pays}")
                continue

            if uid == ADMIN_ID and text == "/payments":
                cur.execute("""
                SELECT id,user_id,plan,tracking_code
                FROM payments
                WHERE status=0
                ORDER BY id DESC
                LIMIT 20
                """)
                rows = cur.fetchall()

                if not rows:
                    send(chat_id,"موردی نیست")
                else:
                    send(chat_id,"\n".join(
                        f"{i} | {u} | {p} | {t}"
                        for i,u,p,t in rows
                    ))
                continue

            if uid == ADMIN_ID and text.startswith("/approve"):
                p = text.split()

                if len(p) != 3:
                    send(chat_id,"/approve payment_id days")
                    continue

                pid = int(p[1])
                days = int(p[2])

                cur.execute("SELECT user_id FROM payments WHERE id=?", (pid,))
                row = cur.fetchone()

                if not row:
                    send(chat_id,"یافت نشد")
                    continue

                target = row[0]

                vip_until = max(now, get_user(target)[1]) + days*86400

                cur.execute(
                    "UPDATE users SET vip_until=? WHERE user_id=?",
                    (vip_until,target)
                )

                cur.execute(
                    "UPDATE payments SET status=1 WHERE id=?",
                    (pid,)
                )

                db.commit()

                send(target,"⭐ VIP شما فعال شد.")
                send(chat_id,"تایید شد.")
                continue

            is_vip = vip > now

            if not is_vip and q >= 3:
                send(chat_id,"اعتبار رایگان تمام شده است.\nخرید vip")
                continue

            try:
                answer = ask_ai(uid, text)

                add_history(uid,"user",text)
                add_history(uid,"assistant",answer)

                if not is_vip:
                    cur.execute(
                        "UPDATE users SET questions=questions+1 WHERE user_id=?",
                        (uid,)
                    )
                    db.commit()

                send(chat_id, answer)

            except Exception as e:
                send(chat_id, f"خطا: {e}")

    except Exception as e:
        print("ERR", e)
        time.sleep(5)
