import requests
import time
import threading

TOKEN = "RUBIKA_TOKEN"
BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

offset = None
lock = threading.Lock()


# ================= ارسال پیام =================
def send_message(chat_id, text, keyboard=None):
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        payload["reply_markup"] = keyboard

    try:
        requests.post(
            f"{BASE_URL}/sendMessage",
            json=payload,
            timeout=10
        )
    except Exception as e:
        print("Send error:", e)


# ================= پردازش پیام =================
def handle_message(chat_id, text):
    print("User:", text)

    if text == "/start":
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "👋 سلام", "callback_data": "hello"},
                    {"text": "ℹ️ اطلاعات", "callback_data": "info"}
                ]
            ]
        }
        send_message(chat_id, "🤖 بات فعال شد!\nیک گزینه انتخاب کن:", keyboard)

    elif text == "سلام":
        send_message(chat_id, "👋 سلام! خوبی؟")

    else:
        send_message(chat_id, "❓ دستور ناشناخته")


# ================= پردازش Callback =================
def handle_callback(chat_id, data_cb):
    print("Callback:", data_cb)

    if data_cb == "hello":
        send_message(chat_id, "سلام 👋 خوش اومدی!")
    elif data_cb == "info":
        send_message(chat_id, "🤖 این یک بات سریع با Multi-thread است")
    else:
        send_message(chat_id, "❓ گزینه نامشخص")


# ================= Thread برای پیام =================
def process_update(u):
    if u["type"] == "NewMessage":
        msg = u["new_message"]
        text = msg.get("text", "")
        chat_id = u["chat_id"]

        handle_message(chat_id, text)

    elif u["type"] == "CallbackQuery":
        chat_id = u["chat_id"]
        data_cb = u["callback_query"].get("data", "")

        handle_callback(chat_id, data_cb)


# ================= دریافت آپدیت‌ها =================
def get_updates():
    global offset

    while True:
        try:
            res = requests.post(
                f"{BASE_URL}/getUpdates",
                json={"offset_id": offset} if offset else {},
                timeout=10
            )

            data = res.json()

            if data.get("status") == "OK":
                updates = data["data"]["updates"]

                for u in updates:
                    offset = u.get("update_time", offset)

                    # 🔥 اجرای هر آپدیت در Thread جدا
                    t = threading.Thread(target=process_update, args=(u,))
                    t.start()

        except Exception as e:
            print("Loop error:", e)

        time.sleep(0.2)  # خیلی سریع‌تر از قبل


# ================= اجرای بات =================
if __name__ == "__main__":
    print("Bot started...")
    get_updates()