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
state TEXT DEFAULT ''
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS payments(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
plan TEXT,
tracking TEXT,
status INTEGER DEFAULT 0,
amount INTEGER DEFAULT 0,
paid_at INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS memory(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
role TEXT,
text TEXT
)
""")

db.commit()

# ================= SEND =================
def send(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text[:4000]}
    if reply_markup:
        data["reply_markup"] = reply_markup
    requests.post(f"{BASE_URL}/sendMessage", json=data)

# ================= USER =================
def get_user(uid):
    cur.execute("SELECT questions,vip_until,last_message,state FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO users(user_id) VALUES(?)", (uid,))
        db.commit()
        return (0, 0, 0, "")
    return row

def set_state(uid, state):
    cur.execute("UPDATE users SET state=? WHERE user_id=?", (state, uid))
    db.commit()

def update_last(uid, now):
    cur.execute("UPDATE users SET last_message=? WHERE user_id=?", (now, uid))
    db.commit()

# ================= MEMORY AI =================
def save_memory(uid, role, text):
    cur.execute("INSERT INTO memory(user_id,role,text) VALUES(?,?,?)", (uid, role, text[:2000]))
    db.commit()

def get_memory(uid):
    cur.execute("""
        SELECT role,text FROM memory
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
    """, (uid,))
    return cur.fetchall()[::-1]

def ask_ai(uid, text):
    msgs = [{"role": "system", "content": "تو یک دستیار فارسی حرفه‌ای هستی."}]

    for r, t in get_memory(uid):
        msgs.append({"role": r, "content": t})

    msgs.append({"role": "user", "content": text})

    res = client.chat.completions.create(
        model="Qwen/Qwen3-8B",
        messages=msgs,
        max_tokens=350
    )

    answer = res.choices[0].message.content

    save_memory(uid, "user", text)
    save_memory(uid, "assistant", answer)

    return answer

# ================= VIP SYSTEM =================
PLAN_DAYS = {
    "vip_1": 1,
    "vip_7": 7,
    "vip_30": 30,
    "vip_365": 365
}

def activate_vip(uid, plan):
    days = PLAN_DAYS.get(plan, 0)
    now = int(time.time())

    cur.execute("SELECT vip_until FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()

    old = row[0] if row else 0

    new_vip = max(now, old) + days * 86400

    cur.execute("""
        UPDATE users SET vip_until=?
        WHERE user_id=?
    """, (new_vip, uid))

    db.commit()

# ================= REVENUE =================
def total_revenue():
    cur.execute("SELECT SUM(amount) FROM payments WHERE status=1")
    return cur.fetchone()[0] or 0

def today_revenue():
    cur.execute("SELECT SUM(amount) FROM payments WHERE status=1 AND paid_at>?", (time.time()-86400,))
    return cur.fetchone()[0] or 0

def month_revenue():
    cur.execute("SELECT SUM(amount) FROM payments WHERE status=1 AND paid_at>?", (time.time()-30*86400,))
    return cur.fetchone()[0] or 0

def vip_count():
    cur.execute("SELECT COUNT(*) FROM users WHERE vip_until>?", (time.time(),))
    return cur.fetchone()[0]

# ================= UI =================
def start_menu(chat_id):
    send(chat_id,
         "👋 خوش آمدید",
         reply_markup={
             "inline_keyboard": [
                 [{"text": "👤 پروفایل", "callback_data": "profile"}],
                 [{"text": "💎 خرید VIP", "callback_data": "vip_menu"}],
                 [{"text": "🤖 چت AI", "callback_data": "ai"}],
                 [{"text": "🧑‍💻 پشتیبانی", "url": "https://t.me/ahmmad24"}]
             ]
         })

def vip_menu(chat_id):
    send(chat_id, "💎 انتخاب پلن:",
         reply_markup={
             "inline_keyboard": [
                 [{"text": "📅 روزانه - 10k", "callback_data": "vip_1"}],
                 [{"text": "📆 هفتگی - 50k", "callback_data": "vip_7"}],
                 [{"text": "🗓 ماهانه - 150k", "callback_data": "vip_30"}],
                 [{"text": "💎 سالانه - 1M", "callback_data": "vip_365"}],
             ]
         })

def admin_dashboard(chat_id):
    send(chat_id,
         f"""
👑 داشبورد درآمد

💰 کل: {total_revenue()}
📅 امروز: {today_revenue()}
📆 ماه: {month_revenue()}

👥 VIP فعال: {vip_count()}
""",
         reply_markup={
             "inline_keyboard": [
                 [{"text": "💳 پرداخت‌ها", "callback_data": "admin_payments"}],
                 [{"text": "📊 رفرش", "callback_data": "admin_stats"}]
             ]
         })

# ================= MAIN =================
print("BOT STARTED")

offset = 0

while True:
    try:
        data = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": offset, "timeout": 30}
        ).json()

        for upd in data.get("result", []):

            offset = upd["update_id"] + 1

            # ============ CALLBACK ============
            if "callback_query" in upd:
                cq = upd["callback_query"]
                d = cq["data"]
                chat_id = cq["message"]["chat"]["id"]
                uid = cq["from"]["id"]

                if d == "vip_menu":
                    vip_menu(chat_id)
                    continue

                if d in PLAN_DAYS:
                    set_state(uid, d)
                    send(chat_id, f"💳 کارت:\n{CARD}\n\n📩 کد پرداخت را ارسال کنید")
                    continue

                if d == "profile":
                    q, vip, last, st = get_user(uid)
                    send(chat_id,
                         f"👤 پروفایل\n📊 سوالات: {q}\n💎 VIP: {'فعال' if vip>time.time() else 'غیرفعال'}")
                    continue

                if d == "ai":
                    set_state(uid, "ai")
                    send(chat_id, "🤖 AI فعال شد")
                    continue

                # ===== ADMIN =====
                if uid == ADMIN_ID:

                    if d == "admin_stats":
                        admin_dashboard(chat_id)
                        continue

                    if d == "admin_payments":
                        rows = cur.execute("""
                            SELECT id,user_id,plan,tracking
                            FROM payments
                            WHERE status=0
                            ORDER BY id DESC
                            LIMIT 10
                        """).fetchall()

                        buttons = []
                        text = "💳 پرداخت‌ها:\n\n"

                        for i,u,p,t in rows:
                            text += f"{i} | {u} | {p} | {t}\n"
                            buttons.append([{
                                "text": f"✅ تایید {i}",
                                "callback_data": f"ok_{i}"
                            }])

                        send(chat_id, text if rows else "خالی",
                             reply_markup={"inline_keyboard": buttons})
                        continue

                    if d.startswith("ok_"):
                        pid = int(d.split("_")[1])

                        cur.execute("SELECT user_id,plan FROM payments WHERE id=?", (pid,))
                        row = cur.fetchone()

                        if row:
                            uid2, plan = row

                            activate_vip(uid2, plan)

                            cur.execute("""
                                UPDATE payments
                                SET status=1,
                                    amount=100000,
                                    paid_at=?
                                WHERE id=?
                            """, (int(time.time()), pid))

                            db.commit()

                            send(uid2, "🎉 VIP فعال شد!")
                            send(chat_id, "✅ تایید شد")

                        continue

                continue

            # ============ MESSAGE ============
            if "message" not in upd:
                continue

            msg = upd["message"]
            uid = msg["from"]["id"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text","").strip()

            if not text:
                continue

            q,vip,last,state = get_user(uid)

            now = int(time.time())

            if uid != ADMIN_ID and now-last<3:
                send(chat_id, "⏳ صبر کن")
                continue

            update_last(uid, now)

            # ===== START =====
            if text == "/start":
                start_menu(chat_id)
                continue

            # ===== ADMIN =====
            if text == "/admin" and uid == ADMIN_ID:
                admin_dashboard(chat_id)
                continue

            # ===== LIMIT =====
            if vip < now and q >= 5:
                send(chat_id,
                     "🚫 محدود شدی",
                     reply_markup={
                         "inline_keyboard":[
                             [{"text":"💎 خرید VIP","callback_data":"vip_menu"}]
                         ]
                     })
                continue

            # ===== PAYMENT INPUT =====
            if state in PLAN_DAYS:

                cur.execute("""
                    INSERT INTO payments(user_id,plan,tracking)
                    VALUES(?,?,?)
                """,(uid,state,text))
                db.commit()

                set_state(uid,"")

                send(chat_id,"✅ ثبت شد")
                send(ADMIN_ID,f"💳\n{uid}\n{state}\n{text}")
                continue

            # ===== AI =====
            try:
                answer = ask_ai(uid,text)
                send(chat_id,answer)
            except:
                send(chat_id,"❌ خطا")

    except Exception as e:
        print("ERR:",e)
        time.sleep(3)
