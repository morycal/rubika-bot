import requests
import time
import sqlite3
import os
from datetime import datetime

# ================= CONFIG =================
TOKEN = "1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"
ADMIN_ID = 586110315

offset = 0

# ================= STORAGE =================
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ================= DATABASE =================
conn = sqlite3.connect("azki.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    chat_id INTEGER PRIMARY KEY,
    name TEXT,
    phone TEXT,
    created_at TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    insurance_type TEXT,
    data TEXT,
    status TEXT,
    created_at TEXT
)
""")

conn.commit()

# ================= STATE =================
state = {}

# ================= SEND =================
def send(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(f"{BASE_URL}/sendMessage", json=payload)

# ================= KEYBOARDS =================
def main_menu():
    return {
        "inline_keyboard": [
            [{"text": "🛒 سفارش بیمه", "callback_data": "buy"}],
            [{"text": "📦 سفارشات من", "callback_data": "orders"}],
            [{"text": "👤 پروفایل", "callback_data": "profile"}]
        ]
    }

def insurance_menu():
    return {
        "inline_keyboard": [
            [{"text": "🚗 شخص ثالث خودرو", "callback_data": "car_third"}],
            [{"text": "🏍 شخص ثالث موتور", "callback_data": "bike_third"}],
            [{"text": "🚙 بدنه خودرو", "callback_data": "car_body"}],
            [{"text": "💖 بیمه عمر", "callback_data": "life"}],
            [{"text": "✈️ مسافرتی", "callback_data": "travel"}],
            [{"text": "🏠 خانه", "callback_data": "home"}],
            [{"text": "🔙 بازگشت", "callback_data": "back"}]
        ]
    }

# ================= BOT =================
print("🚀 AZKI 2 BOT RUNNING")

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

            # ================= MESSAGE =================
            if "message" in u:
                msg = u["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "").strip()

                # -------- START --------
                if text == "/start":
                    user = cur.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,)).fetchone()

                    if user:
                        send(chat_id, f"👋 خوش برگشتی {user[1]}", main_menu())
                    else:
                        state[chat_id] = {"step": "name"}
                        send(chat_id, "👋 به ازکی بیمه خوش آمدی\nنام و نام خانوادگی را وارد کن:")
                    continue

                # -------- REGISTER --------
                if chat_id in state:
                    step = state[chat_id]["step"]

                    if step == "name":
                        state[chat_id]["name"] = text
                        state[chat_id]["step"] = "phone"
                        send(chat_id, "📱 شماره موبایل:")
                        continue

                    elif step == "phone":
                        state[chat_id]["phone"] = text

                        cur.execute("""
                            INSERT OR REPLACE INTO users(chat_id, name, phone, created_at)
                            VALUES (?,?,?,?)
                        """, (
                            chat_id,
                            state[chat_id]["name"],
                            text,
                            datetime.now().isoformat()
                        ))
                        conn.commit()

                        send(chat_id, "✅ ثبت‌نام کامل شد", main_menu())
                        send(ADMIN_ID, f"👤 کاربر جدید:\n{state[chat_id]['name']}\n{text}")

                        state.pop(chat_id)
                        continue

            # ================= CALLBACK =================
            if "callback_query" in u:
                cb = u["callback_query"]
                chat_id = cb["message"]["chat"]["id"]
                data = cb["data"]

                # -------- MAIN --------
                if data == "back":
                    send(chat_id, "🏠 منو اصلی", main_menu())

                elif data == "buy":
                    send(chat_id, "🛒 نوع بیمه را انتخاب کن:", insurance_menu())

                elif data == "profile":
                    user = cur.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,)).fetchone()
                    send(chat_id, f"👤 پروفایل:\n{name if (name:=user[1]) else ''}\n📱 {user[2]}" if user else "❌")

                elif data == "orders":
                    rows = cur.execute("SELECT id, insurance_type, status FROM orders WHERE chat_id=?", (chat_id,)).fetchall()

                    msg = "📦 سفارشات:\n\n"
                    for r in rows:
                        msg += f"#{r[0]} | {r[1]} | {r[2]}\n"

                    send(chat_id, msg)

                # -------- INSURANCE --------
                elif data.startswith("car_") or data.startswith("bike_") or data in ["life", "travel", "home"]:

                    types = {
                        "car_third": "شخص ثالث خودرو",
                        "bike_third": "شخص ثالث موتور",
                        "car_body": "بدنه خودرو",
                        "life": "عمر",
                        "travel": "مسافرتی",
                        "home": "خانه"
                    }

                    ins = types.get(data, "نامشخص")

                    cur.execute("""
                        INSERT INTO orders(chat_id, insurance_type, data, status, created_at)
                        VALUES (?,?,?,?,?)
                    """, (
                        chat_id,
                        ins,
                        "{}",
                        "pending",
                        datetime.now().isoformat()
                    ))
                    conn.commit()

                    order_id = cur.lastrowid

                    send(chat_id, f"✅ سفارش ثبت شد #{order_id}\nکارشناس بررسی می‌کند")
                    send(ADMIN_ID, f"🆕 سفارش جدید #{order_id}\nنوع: {ins}\nکاربر: {chat_id}")

                # -------- ADMIN (SIMPLE PANEL) --------
                if chat_id == ADMIN_ID:

                    if data == "admin_users":
                        rows = cur.execute("SELECT name, phone FROM users ORDER BY rowid DESC LIMIT 10").fetchall()
                        msg = "👥 کاربران:\n\n"
                        for r in rows:
                            msg += f"{r[0]} | {r[1]}\n"
                        send(chat_id, msg)

                    elif data == "admin_orders":
                        rows = cur.execute("SELECT id, insurance_type, status FROM orders ORDER BY id DESC LIMIT 10").fetchall()
                        msg = "📦 سفارشات:\n\n"
                        for r in rows:
                            msg += f"#{r[0]} | {r[1]} | {r[2]}\n"
                        send(chat_id, msg)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
