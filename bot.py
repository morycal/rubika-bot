import requests
import time
import sqlite3
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
    {"id": 1, "name": "کفش اسپرت", "price": 250000},
    {"id": 2, "name": "تی‌شرت", "price": 120000},
    {"id": 3, "name": "هدفون", "price": 500000},
    {"id": 4, "name": "کوله‌پشتی", "price": 300000},
]

# ---------------- SEND ----------------

def send(chat_id, text):
    try:
        requests.post(
            f"{BASE_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text}
        )
    except:
        pass

# ---------------- CART ----------------

def add_to_cart(user_id, product):
    cur.execute(
        "INSERT INTO cart VALUES (?,?,?,?)",
        (user_id, product["name"], product["price"], 1)
    )
    conn.commit()

def get_cart(user_id):
    cur.execute(
        "SELECT product, price, qty FROM cart WHERE user_id=?",
        (user_id,)
    )
    return cur.fetchall()

def clear_cart(user_id):
    cur.execute("DELETE FROM cart WHERE user_id=?", (user_id,))
    conn.commit()

# ---------------- PRODUCTS LIST ----------------

def product_list():
    msg = "🛍 محصولات:\n\n"
    for p in products:
        msg += f"{p['id']}. {p['name']} - {p['price']} تومان\n"
    msg += "\n🔹 شماره محصول را ارسال کن"
    return msg

# ---------------- LOOP ----------------

print("🚀 LIGHT SHOP BOT STARTED")

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

            if "message" not in update:
                continue

            msg = update["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "").strip()

            # ---------------- START ----------------
            if text == "/start":
                send(chat_id,
                     "👋 به فروشگاه حرفه‌ای خوش اومدی!\n\n"
                     "📌 دستورات:\n"
                     "🛍 محصولات\n"
                     "🛒 سبد\n"
                     "💳 پرداخت\n"
                     "📊 آمار")

            # ---------------- PRODUCTS ----------------
            elif text == "محصولات":
                send(chat_id, product_list())

            # ---------------- ADD TO CART ----------------
            elif text.isdigit():
                pid = int(text)
                product = next((p for p in products if p["id"] == pid), None)

                if product:
                    add_to_cart(chat_id, product)
                    send(chat_id, f"➕ اضافه شد: {product['name']}")

            # ---------------- CART ----------------
            elif text == "سبد":
                items = get_cart(chat_id)

                if not items:
                    send(chat_id, "🛒 سبدت خالیه ❌")
                else:
                    msg_txt = "🛒 سبد خرید:\n\n"
                    total = 0

                    for item in items:
                        name, price, qty = item
                        total += price * qty
                        msg_txt += f"📦 {name} x{qty} = {price*qty}\n"

                    msg_txt += f"\n💰 مجموع: {total}"
                    send(chat_id, msg_txt)

            # ---------------- PAYMENT ----------------
            elif text == "پرداخت":
                items = get_cart(chat_id)

                if not items:
                    send(chat_id, "❌ سبد خرید خالی است")
                else:
                    total = 0
                    invoice = "🧾 فاکتور شما:\n\n"

                    for item in items:
                        name, price, qty = item
                        total += price * qty
                        invoice += f"📦 {name} x{qty} = {price*qty}\n"

                    invoice += f"\n💰 مبلغ قابل پرداخت: {total}"

                    send(chat_id,
                         "💳 پرداخت موفق (شبیه‌سازی شده)\n\n" + invoice)

                    # ارسال به ادمین
                    send(ADMIN_ID,
                         f"🆕 سفارش جدید\nUser: {chat_id}\nTotal: {total}")

                    # ذخیره سفارش
                    cur.execute(
                        "INSERT INTO orders (user_id,total,date) VALUES (?,?,?)",
                        (chat_id, total, str(datetime.now()))
                    )
                    conn.commit()

                    clear_cart(chat_id)

            # ---------------- ADMIN ----------------
            elif text == "آمار" and chat_id == ADMIN_ID:
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
