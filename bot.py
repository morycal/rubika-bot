import requests
import time
import sqlite3

TOKEN = "1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

ADMIN_ID = 586110315

offset = 0

# ---------------- DB ----------------
conn = sqlite3.connect("insurance.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    service TEXT,
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

# ---------------- ADMIN MENU ----------------
def admin_menu():
    return {
        "inline_keyboard": [
            [{"text": "📊 آمار فروش", "callback_data": "admin_stats"}],
            [{"text": "📦 آخرین سفارش‌ها", "callback_data": "admin_orders"}],
            [{"text": "🔄 تغییر وضعیت سفارش", "callback_data": "admin_status"}],
            [{"text": "📣 پیام به کاربر", "callback_data": "admin_msg"}]
        ]
    }

# ---------------- BOT ----------------
print("🚀 ADMIN PANEL STARTED")

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
                text = msg.get("text", "")

                # ---------- ADMIN ENTRY ----------
                if text == "/start" and chat_id == ADMIN_ID:
                    send(chat_id, "👑 پنل مدیریت بیمه", admin_menu())

                elif chat_id == ADMIN_ID and chat_id in state:

                    # پیام ادمین به کاربر
                    if state[chat_id].get("mode") == "send_msg":
                        target = state[chat_id]["target"]

                        send(target, f"📣 پیام از پشتیبانی:\n\n{text}")
                        send(chat_id, "✅ پیام ارسال شد")
                        state.pop(chat_id)

                    # تغییر وضعیت سفارش
                    elif state[chat_id].get("mode") == "change_status":
                        order_id = state[chat_id]["order_id"]

                        cur.execute("""
                            UPDATE orders SET status=? WHERE id=?
                        """, (text, order_id))
                        conn.commit()

                        send(chat_id, "✅ وضعیت بروزرسانی شد")
                        state.pop(chat_id)

            # ---------------- CALLBACK ----------------
            if "callback_query" in u:
                cb = u["callback_query"]
                chat_id = cb["message"]["chat"]["id"]
                data = cb["data"]

                if chat_id != ADMIN_ID:
                    continue

                # ---------- STATS ----------
                if data == "admin_stats":
                    cur.execute("SELECT COUNT(*), SUM(price) FROM orders")
                    res = cur.fetchone()

                    send(chat_id,
                         f"📊 آمار فروش\n\n"
                         f"📦 سفارش‌ها: {res[0]}\n"
                         f"💰 درآمد: {res[1] or 0}")

                # ---------- ORDERS ----------
                elif data == "admin_orders":
                    cur.execute("""
                        SELECT id, user_id, service, plan, price, status
                        FROM orders
                        ORDER BY id DESC
                        LIMIT 10
                    """)

                    rows = cur.fetchall()

                    msg = "📦 آخرین سفارش‌ها:\n\n"
                    for r in rows:
                        msg += f"#{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]}\n"

                    send(chat_id, msg)

                # ---------- CHANGE STATUS ----------
                elif data == "admin_status":
                    state[chat_id] = {"mode": "change_status", "order_id": 1}
                    send(chat_id, "🔢 شماره سفارش را وارد کنید:")

                # ---------- SEND MESSAGE ----------
                elif data == "admin_msg":
                    state[chat_id] = {"mode": "send_msg"}
                    send(chat_id, "🆔 آیدی کاربر + پیام را ارسال کنید:")
