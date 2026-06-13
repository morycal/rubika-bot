import requests
import time
import sqlite3
from datetime import datetime

TOKEN = "1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

ADMIN_ID = 586110315  # ← این را با chat_id خودت جایگزین کن

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
]


# ---------------- SEND ----------------

def send(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    requests.post(f"{BASE_URL}/sendMessage", json=payload)


# ---------------- KEYBOARDS ----------------

def main_menu():
    return {
        "inline_keyboard": [
            [{"text": "🛍 محصولات", "callback_data": "products"}],
            [{"text": "🛒 سبد خرید", "callback_data": "cart"}],
            [{"text": "💳 پرداخت", "callback_data": "pay"}],
            [{"text": "📊 آمار", "callback_data": "admin"}]
        ]
    }


def products_keyboard():
    buttons = []
    for p in products:
        buttons.append([{
            "text": f"{p['name']} - {p['price']} تومان",
            "callback_data": f"add_{p['id']}"
        }])
    buttons.append([{"text": "🔙 بازگشت", "callback_data": "back"}])
    return {"inline_keyboard": buttons}


def qty_keyboard(pid):
    return {
        "inline_keyboard": [
            [
                {"text": "1", "callback_data": f"qty_{pid}_1"},
                {"text": "2", "callback_data": f"qty_{pid}_2"},
                {"text": "3", "callback_data": f"qty_{pid}_3"}
            ],
            [
                {"text": "5", "callback_data": f"qty_{pid}_5"},
                {"text": "10", "callback_data": f"qty_{pid}_10"}
            ]
        ]
    }


# ---------------- CART ----------------

def add_to_cart(user_id, product, qty=1):
    cur.execute(
        "INSERT INTO cart VALUES (?,?,?,?)",
        (user_id, product["name"], product["price"], qty)
    )
    conn.commit()


def get_cart(user_id):
    cur.execute("SELECT product, price, qty FROM cart WHERE user_id=?", (user_id,))
    return cur.fetchall()


def clear_cart(user_id):
    cur.execute("DELETE FROM cart WHERE user_id=?", (user_id,))
    conn.commit()


# ---------------- LOOP ----------------

print("🚀 INLINE SHOP BOT STARTED")

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

                if text == "/start":
                    send(
                        chat_id,
                        "👋 به فروشگاه حرفه‌ای خوش اومدی!\n"
                        "👇 یکی از گزینه‌ها رو انتخاب کن:",
                        main_menu()
                    )

            # ---------------- CALLBACK ----------------
            if "callback_query" in update:
                cb = update["callback_query"]
                chat_id = cb["message"]["chat"]["id"]
                data_cb = cb["data"]

                # ---- MENU ----
                if data_cb == "back":
                    send(chat_id, "🏠 منو اصلی", main_menu())

                elif data_cb == "products":
                    send(chat_id, "🛍 لیست محصولات:", products_keyboard())

                elif data_cb.startswith("add_"):
                    pid = int(data_cb.split("_")[1])
                    product = next(p for p in products if p["id"] == pid)

                    send(
                        chat_id,
                        f"📦 {product['name']}\n💰 {product['price']}\n\nتعداد را انتخاب کن:",
                        qty_keyboard(pid)
                    )

                elif data_cb.startswith("qty_"):
                    _, pid, qty = data_cb.split("_")
                    pid = int(pid)
                    qty = int(qty)

                    product = next(p for p in products if p["id"] == pid)

                    add_to_cart(chat_id, product, qty)

                    send(chat_id,
                         f"✅ اضافه شد:\n{product['name']} x{qty}",
                         main_menu())

                # ---- CART ----
                elif data_cb == "cart":
                    items = get_cart(chat_id)

                    if not items:
                        send(chat_id, "🛒 سبد خرید خالیه ❌", main_menu())
                    else:
                        msg = "🛒 سبد خرید:\n\n"
                        total = 0

                        for i in items:
                            name, price, qty = i
                            total += price * qty
                            msg += f"📦 {name} x{qty} = {price*qty}\n"

                        msg += f"\n💰 مجموع: {total}"
                        send(chat_id, msg, main_menu())

                # ---- PAYMENT ----
                elif data_cb == "pay":
                    items = get_cart(chat_id)

                    if not items:
                        send(chat_id, "❌ سبد خالیه", main_menu())
                    else:
                        total = 0
                        for i in items:
                            total += i[1] * i[2]

                        send(chat_id,
                             f"💳 پرداخت انجام شد (شبیه‌سازی)\n💰 مبلغ: {total}")

                        send(ADMIN_ID,
                             f"🆕 سفارش جدید\nUser: {chat_id}\nTotal: {total}")

                        cur.execute(
                            "INSERT INTO orders (user_id,total,date) VALUES (?,?,?)",
                            (chat_id, total, str(datetime.now()))
                        )
                        conn.commit()

                        clear_cart(chat_id)

                        send(chat_id, "🎉 سفارش ثبت شد", main_menu())

                # ---- ADMIN ----
                elif data_cb == "admin":
                    if chat_id == ADMIN_ID:
                        cur.execute("SELECT COUNT(*), SUM(total) FROM orders")
                        data = cur.fetchone()

                        send(chat_id,
                             f"📊 آمار فروش:\n"
                             f"🧾 سفارشات: {data[0]}\n"
                             f"💰 درآمد: {data[1]}",
                             main_menu())
                    else:
                        send(chat_id, "⛔ دسترسی نداری")

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
