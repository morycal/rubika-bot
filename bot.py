import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.environ.get("1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c")

# آیدی عددی ادمین (از بله)
ADMIN_ID = os.environ.get("586110315")

# وضعیت کاربران
user_state = {}

def send_message(chat_id, text):
    url = f"https://tapi.bale.ai/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": text
    })


def send_to_admin(text):
    url = f"https://tapi.bale.ai/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": ADMIN_ID,
        "text": text
    })


def main_menu(chat_id):
    send_message(chat_id,
"""
🏢 ثبت سفارش بیمه

1️⃣ بیمه شخص ثالث
2️⃣ بیمه بدنه
3️⃣ بیمه عمر
4️⃣ بیمه درمان

لطفاً نوع بیمه را انتخاب کنید:
"""
    )


@app.route("/", methods=["GET"])
def home():
    return "Bale Insurance Bot Running"


@app.route("/", methods=["POST"])
def webhook():

    data = request.json

    if "message" not in data:
        return jsonify({"ok": True})

    msg = data["message"]
    chat_id = str(msg["chat"]["id"])
    text = msg.get("text", "").strip()

    # شروع
    if text == "/start":
        user_state[chat_id] = {"step": "insurance_type"}
        main_menu(chat_id)

    # انتخاب نوع بیمه
    elif chat_id in user_state and user_state[chat_id]["step"] == "insurance_type":

        user_state[chat_id]["insurance"] = text
        user_state[chat_id]["step"] = "name"

        send_message(chat_id, "نام و نام خانوادگی را وارد کنید:")

    # نام
    elif chat_id in user_state and user_state[chat_id]["step"] == "name":

        user_state[chat_id]["name"] = text
        user_state[chat_id]["step"] = "phone"

        send_message(chat_id, "شماره تماس را وارد کنید:")

    # شماره
    elif chat_id in user_state and user_state[chat_id]["step"] == "phone":

        user_state[chat_id]["phone"] = text
        user_state[chat_id]["step"] = "desc"

        send_message(chat_id, "توضیحات (در صورت نیاز) را وارد کنید:")

    # توضیحات + ثبت نهایی
    elif chat_id in user_state and user_state[chat_id]["step"] == "desc":

        user_state[chat_id]["desc"] = text

        data_user = user_state.pop(chat_id)

        order_text = f"""
📥 سفارش جدید بیمه

👤 نام: {data_user['name']}
📱 موبایل: {data_user['phone']}
🏷 نوع بیمه: {data_user['insurance']}
📝 توضیحات: {data_user['desc']}
"""

        # ارسال به ادمین
        send_to_admin(order_text)

        # پیام به کاربر
        send_message(chat_id,
"""
✅ سفارش شما ثبت شد

به زودی کارشناسان ما با شما تماس می‌گیرند 📞
"""
        )

    else:
        send_message(chat_id, "برای شروع /start را بزن")

    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
