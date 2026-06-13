import requests
import time

TOKEN = "1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0

products = [
    {"id": 1, "name": "کفش ورزشی", "price": 250000},
    {"id": 2, "name": "تی‌شرت", "price": 120000},
    {"id": 3, "name": "هدفون", "price": 500000},
]

user_state = {}
orders = []


# ---------------- SEND MESSAGE ----------------

def send(chat_id, text, reply_markup=None, reply_to=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    if reply_to:
        payload["reply_to_message_id"] = reply_to

    requests.post(f"{BASE_URL}/sendMessage", json=payload)


# ---------------- INLINE KEYBOARD ----------------

def product_keyboard():
    buttons = []

    for p in products:
        buttons.append([
            {
                "text": f"{p['name']} - {p['price']} تومان",
                "callback_data": f"product_{p['id']}"
            }
        ])

    return {"inline_keyboard": buttons}


def qty_keyboard(pid):
    return {
        "inline_keyboard": [
            [
                {"text": "1️⃣", "callback_data": f"qty_{pid}_1"},
                {"text": "2️⃣", "callback_data": f"qty_{pid}_2"},
                {"text": "3️⃣", "callback_data": f"qty_{pid}_3"}
            ],
            [
                {"text": "5️⃣", "callback_data": f"qty_{pid}_5"},
                {"text": "10️⃣", "callback_data": f"qty_{pid}_10"}
            ]
        ]
    }


# ---------------- MAIN ----------------

print("🚀 PRO SHOP BOT STARTED")

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
                    send(
                        chat_id,
                        "🛍 به فروشگاه حرفه‌ای خوش اومدی!\n\n"
                        "👇 یکی از محصولات رو انتخاب کن:",
                        reply_markup=product_keyboard(),
                        reply_to=msg_id
                    )

                elif text == "سفارشات":
                    user_orders = [o for o in orders if o["chat_id"] == chat_id]

                    if not user_orders:
                        send(chat_id, "❌ هیچ سفارشی نداری", msg_id)
                    else:
                        msg_txt = "📋 سفارشات شما:\n\n"
                        for o in user_orders:
                            msg_txt += f"📦 {o['product']} | {o['qty']} عدد | {o['total']} تومان\n"

                        send(chat_id, msg_txt, msg_id)

            # ---------------- CALLBACK (BUTTON CLICK) ----------------
            if "callback_query" in update:
                cb = update["callback_query"]
                chat_id = cb["message"]["chat"]["id"]
                data_cb = cb["data"]

                # انتخاب محصول
                if data_cb.startswith("product_"):
                    pid = int(data_cb.split("_")[1])

                    product = next(p for p in products if p["id"] == pid)

                    user_state[chat_id] = product

                    send(
                        chat_id,
                        f"📦 محصول انتخاب شد:\n\n"
                        f"🔹 {product['name']}\n"
                        f"💰 {product['price']} تومان\n\n"
                        f"👇 حالا تعداد را انتخاب کن:",
                        reply_markup=qty_keyboard(pid)
                    )

                # انتخاب تعداد
                elif data_cb.startswith("qty_"):
                    _, pid, qty = data_cb.split("_")

                    pid = int(pid)
                    qty = int(qty)

                    product = next(p for p in products if p["id"] == pid)

                    total = product["price"] * qty

                    orders.append({
                        "chat_id": chat_id,
                        "product": product["name"],
                        "qty": qty,
                        "total": total
                    })

                    send(
                        chat_id,
                        "✅ سفارش ثبت شد!\n\n"
                        f"📦 محصول: {product['name']}\n"
                        f"🔢 تعداد: {qty}\n"
                        f"💰 مبلغ: {total} تومان\n\n"
                        "🙏 ممنون از خریدت!"
                    )

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
