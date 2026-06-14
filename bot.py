import requests
import time
import sqlite3
import os
from datetime import datetime

# ---------------- CONFIG ----------------
TOKEN = "1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"
ADMIN_ID = 586110315

offset = 0

# ---------------- FILE STORAGE ----------------
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------- DB ----------------
conn = sqlite3.connect("insurance.db", check_same_thread=False)
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
    type TEXT,
    data TEXT,
    status TEXT,
    created_at TEXT
)
""")

conn.commit()

# ---------------- STATE ----------------
state = {}

# ---------------- SEND ----------------
def send(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = reply_markup
    requests.post(f"{BASE_URL}/sendMessage", json=data)

# ---------------- DOWNLOAD FILE ----------------
def save_file(file_id, file_name):
    file_url = requests.get(f"{BASE_URL}/getFile?file_id={file_id}").json()
    path = file_url["result"]["file_path"]

    file_data = requests.get(f"https://tapi.bale.ai/file/bot{TOKEN}/{path}").content

    full_path = os.path.join(UPLOAD_DIR, file_name)
    with open(full_path, "wb") as f:
        f.write(file_data)

    return full_path

# ---------------- KEYBOARD ----------------
def main_menu():
    return {
        "inline_keyboard": [
            [{"text": "📝 سفارش بیمه", "callback_data": "order"}],
            [{"text": "📦 سفارشات", "callback_data": "orders"}],
            [{"text": "👤 پروفایل", "callback_data": "profile"}]
        ]
    }

def insurance_menu():
    return {
        "inline_keyboard": [
            [{"text": "🚗 شخص ثالث خودرو", "callback_data": "third_car"}],
            [{"text": "🏍 شخص ثالث موتور", "callback_data": "third_bike"}],
            [{"text": "🚙 بدنه خودرو", "callback_data": "body_car"}],
            [{"text": "💖 عمر", "callback_data": "life"}],
            [{"text": "✈️ مسافرتی", "callback_data": "travel"}],
            [{"text": "🔙 بازگشت", "callback_data": "back"}]
        ]
    }

# ---------------- BOT ----------------
print("🚀 Insurance Bot Started")

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
                text = msg.get("text", "")

                # ---- START ----
                if text == "/start":
                    send(chat_id,
                         "👋 به سامانه ازکی بیمه خوش آمدید\nلطفاً گزینه مورد نظر را انتخاب کنید:",
                         main_menu())

                # ---- REGISTER STEP (SIMPLE) ----
                if chat_id in state:
                    step = state[chat_id].get("step")

                    if step == "third_car_plate":
                        state[chat_id]["plate"] = text
                        state[chat_id]["step"] = "third_car_national"
                        send(chat_id, "کد ملی را وارد کنید:")
                        continue

                    elif step == "third_car_national":
                        state[chat_id]["national"] = text
                        state[chat_id]["step"] = "third_car_brand"
                        send(chat_id, "برند خودرو را وارد کنید:")
                        continue

                    elif step == "third_car_brand":
                        state[chat_id]["brand"] = text
                        state[chat_id]["step"] = "third_car_model"
                        send(chat_id, "مدل خودرو را وارد کنید:")
                        continue

                    elif step == "third_car_model":
                        state[chat_id]["model"] = text
                        state[chat_id]["step"] = "third_car_address"
                        send(chat_id, "آدرس را وارد کنید:")
                        continue

                    elif step == "third_car_address":
                        state[chat_id]["address"] = text

                        cur.execute("""
                            INSERT INTO orders(chat_id, type, data, status, created_at)
                            VALUES (?,?,?,?,?)
                        """, (
                            chat_id,
                            "شخص ثالث خودرو",
                            str(state[chat_id]),
                            "pending",
                            datetime.now().isoformat()
                        ))
                        conn.commit()

                        order_id = cur.lastrowid

                        send(chat_id, f"✅ سفارش ثبت شد #{order_id}", main_menu())
                        send(ADMIN_ID, f"🆕 سفارش جدید #{order_id}\n{state[chat_id]}")

                        state.pop(chat_id)
                        continue

            # ================= CALLBACK =================
            if "callback_query" in u:
                cb = u["callback_query"]
                chat_id = cb["message"]["chat"]["id"]
                data = cb["data"]

                # ---- MAIN ----
                if data == "back":
                    send(chat_id, "🏠 منو اصلی", main_menu())

                elif data == "order":
                    send(chat_id, "📝 نوع بیمه را انتخاب کنید:", insurance_menu())

                # ---- THIRD CAR ----
                elif data == "third_car":
                    state[chat_id] = {"step": "third_car_plate"}
                    send(chat_id, "🚗 پلاک خودرو را وارد کنید:")

                elif data == "profile":
                    send(chat_id, f"👤 پروفایل شما:\nID: {chat_id}")

                elif data == "orders":
                    cur.execute("SELECT id, type, status FROM orders WHERE chat_id=?", (chat_id,))
                    rows = cur.fetchall()

                    msg = "📦 سفارشات شما:\n\n"
                    for r in rows:
                        msg += f"#{r[0]} | {r[1]} | {r[2]}\n"

                    send(chat_id, msg or "سفارشی ندارید")

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)

    time.sleep(1)
