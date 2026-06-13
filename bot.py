import requests
import time
import sqlite3
import random
from datetime import datetime
from reportlab.pdfgen import canvas

# ---------------- CONFIG ----------------
TOKEN = "1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"
ADMIN_ID = 586110315

offset = 0

# ---------------- DB ----------------
conn = sqlite3.connect("insurance.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    chat_id INTEGER PRIMARY KEY,
    name TEXT,
    phone TEXT,
    nid TEXT,
    province TEXT,
    address TEXT,
    postal TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    plan TEXT,
    price INTEGER,
    status TEXT
)
""")

conn.commit()

# ---------------- STATE ----------------
state = {}

# ---------------- SEND ----------------
def send(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(f"{BASE_URL}/sendMessage", json=payload)

# ---------------- PDF ----------------
def create_pdf(order_id, user, plan, price):
    file_name = f"policy_{order_id}.pdf"

    policy = f"INS-{random.randint(100000,999999)}"
    date = datetime.now().strftime("%Y-%m-%d %H:%M")

    c = canvas.Canvas(file_name)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(180, 800, "🏢 بیمه‌نامه رسمی")

    c.setFont("Helvetica", 12)
    c.drawString(50, 750, f"شماره بیمه: {policy}")
    c.drawString(50, 730, f"تاریخ: {date}")

    c.drawString(50, 700, f"نام: {user[1]}")
    c.drawString(50, 680, f"موبایل: {user[2]}")
    c.drawString(50, 660, f"کد ملی: {user[3]}")
    c.drawString(50, 640, f"استان: {user[4]}")
    c.drawString(50, 620, f"آدرس: {user[5]}")
    c.drawString(50, 600, f"کد پستی: {user[6]}")

    c.drawString(50, 560, f"پلن: {plan}")
    c.drawString(50, 540, f"قیمت: {price:,} تومان")

    c.drawString(50, 500, "📌 این بیمه‌نامه به صورت دیجیتال صادر شده است.")

    c.save()
    return file_name

# ---------------- SEND FILE ----------------
def send_file(chat_id, path):
    url = f"{BASE_URL}/sendDocument"
    files = {"document": open(path, "rb")}
    data = {"chat_id": chat_id}
    requests.post(url, files=files, data=data)

# ---------------- MENU ----------------
def main_menu():
    return {
        "inline_keyboard": [
            [{"text": "🚗 بیمه خودرو", "callback_data": "car"}],
            [{"text": "🏥 بیمه درمان", "callback_data": "health"}],
            [{"text": "📦 سفارشات من", "callback_data": "orders"}]
        ]
    }

# ---------------- BOT ----------------
print("🚀 INSURANCE FULL SYSTEM STARTED")

while True:
    try:
        res = requests.post(
            f"{BASE_URL}/getUpdates",
            json={"offset": offset},
            timeout=20
        )

        updates = res.json().get("result", [])

        for u in updates:
            offset = u["update_id"] + 1

            # ---------------- MESSAGE ----------------
            if "message" in u:
                msg = u["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "").strip()

                if text == "/start":
                    send(chat_id, "🏢 سامانه بیمه فعال شد", main_menu())

            # ---------------- CALLBACK ----------------
            if "callback_query" in u:
                cb = u["callback_query"]
                chat_id = cb["message"]["chat"]["id"]
                data = cb["data"]

                # ---------------- BUY ----------------
                if data in ["car", "health"]:

                    plan = "خودرو" if data == "car" else "درمان"
                    price = 500000 if data == "car" else 300000

                    cur.execute("""
                        INSERT INTO orders (user_id, plan, price, status)
                        VALUES (?, ?, ?, ?)
                    """, (chat_id, plan, price, "pending"))
                    conn.commit()

                    order_id = cur.lastrowid

                    cur.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,))
                    user = cur.fetchone()

                    if not user:
                        send(chat_id, "❌ ابتدا اطلاعات کاربر را ثبت کنید")
                        continue

                    send(chat_id,
                         f"✅ سفارش ثبت شد\n"
                         f"📦 {plan}\n"
                         f"💰 {price:,} تومان\n"
                         f"⏳ در انتظار پرداخت")

                    send(ADMIN_ID, f"🆕 سفارش جدید #{order_id} از {chat_id}")

                    # --- AUTO PDF (simulate paid) ---
                    file = create_pdf(order_id, user, plan, price)

                    send_file(chat_id, file)
                    send_file(ADMIN_ID, file)

                    cur.execute("UPDATE orders SET status='done' WHERE id=?", (order_id,))
                    conn.commit()

                # ---------------- ORDERS ----------------
                elif data == "orders":
                    cur.execute("SELECT id, plan, price, status FROM orders WHERE user_id=?", (chat_id,))
                    rows = cur.fetchall()

                    if not rows:
                        send(chat_id, "📭 سفارشی ندارید")
                    else:
                        msg = "📦 سفارشات شما:\n\n"
                        for r in rows:
                            msg += f"#{r[0]} | {r[1]} | {r[2]:,} | {r[3]}\n"

                        send(chat_id, msg)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
