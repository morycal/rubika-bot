import requests
import time
import sqlite3
from reportlab.pdfgen import canvas
from datetime import datetime

TOKEN = "1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

ADMIN_ID = 123456789  # آیدی خودت

offset = 0


# ---------------- DATABASE ----------------

conn = sqlite3.connect("shop.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS cart (
    user_id INTEGER,
    product TEXT,
    price INTEGER,
    qty INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    total INTEGER,
    date TEXT
)
""")

conn.commit()


# ---------------- PRODUCTS ----------------

products = [
    {"id": 1, "name": "کفش", "price": 250000},
    {"id": 2, "name": "تی‌شرت", "price": 120000},
    {"id": 3, "name": "هدفون", "price": 500000},
]


# ---------------- SEND ----------------

def send(chat_id, text):
    requests.post(
        f"{BASE_URL}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )


# ---------------- PDF ----------------

def make_invoice(user_id):
    file_name = f"invoice_{user_id}.pdf"

    c = canvas.Canvas(file_name)
    c.drawString(100, 800, "INVOICE - SHOP BOT")

    cur.execute("SELECT product, price, qty FROM cart WHERE user_id=?", (user_id,))
    items = cur.fetchall()

    y = 750
    total = 0

    for item in items:
        name, price, qty = item
        line_total = price * qty
        total += line_total
        c.drawString(100, y, f"{name} x{qty} = {line_total}")
        y -= 30

    c.drawString(100, y-20, f"TOTAL: {total}")

    c.save()

    return file_name, total


# ---------------- CART ----------------

def add_to_cart(user_id, product):
    cur.execute(
        "INSERT INTO cart VALUES (?,?,?,?)",
        (user_id, product["name"], product["price"], 1)
    )
    conn.commit()


def get_cart(user_id):
    cur.execute("SELECT product, price, qty FROM cart WHERE user_id=?", (user_id,))
    return cur.fetchall()


# ---------------- LOOP ----------------

print("🚀 PRO SHOP V2 STARTED")

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

            # ---------------- MESSAGE ----------------
            if "message" in update:
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "")
                msg_id = msg.get("message_id")

                if text == "/start":
                    send(chat_id,
                         "🛍 فروشگاه حرفه‌ای فعال شد\n"
                         "دستورها:\n"
                         "محصولات | سبد | پرداخت | ادمین")

                elif text == "محصولات":
                    msg_txt = "🛍 محصولات:\n\n"
                    for p in products:
                        msg_txt += f"{p['id']}. {p['name']} - {p['price']}\n"
                    send(chat_id, msg_txt)

                elif text.isdigit():
                    pid = int(text)
                    product = next((p for p in products if p["id"] == pid), None)

                    if product:
                        add_to_cart(chat_id, product)
                        send(chat_id, f"➕ اضافه شد: {product['name']}")

                elif text == "سبد":
                    items = get_cart(chat_id)

                    if not items:
                        send(chat_id, "سبد خالیه ❌")
                    else:
                        msg_txt = "🛒 سبد خرید:\n\n"
                        total = 0

                        for i in items:
                            name, price, qty = i
                            total += price * qty
                            msg_txt += f"{name} x{qty} = {price*qty}\n"

                        msg_txt += f"\n💰 مجموع: {total}"
                        send(chat_id, msg_txt)

                elif text == "پرداخت":

                    file, total = make_invoice(chat_id)

                    send(chat_id,
                         f"💳 پرداخت شبیه‌سازی شد\n"
                         f"💰 مبلغ: {total}\n"
                         f"📄 فاکتور ساخته شد")

                    send(ADMIN_ID,
                         f"🆕 سفارش جدید\nUser: {chat_id}\nTotal: {total}")

                    cur.execute(
                        "INSERT INTO orders (user_id,total,date) VALUES (?,?,?)",
                        (chat_id, total, str(datetime.now()))
                    )
                    conn.commit()

                    cur.execute("DELETE FROM cart WHERE user_id=?", (chat_id,))
                    conn.commit()

                elif text == "ادمین" and chat_id == ADMIN_ID:
                    cur.execute("SELECT COUNT(*), SUM(total) FROM orders")
                    data = cur.fetchone()

                    send(chat_id,
                         f"📊 آمار فروش:\n"
                         f"🧾 سفارشات: {data[0]}\n"
                         f"💰 درآمد: {data[1]}")

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
