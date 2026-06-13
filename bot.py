from flask import Flask, request
import requests
import os

app = Flask(__name__)

TOKEN = "YOUR_BALE_BOT_TOKEN"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"


# ---------------- SEND MESSAGE ----------------
def send_message(chat_id, text):
    try:
        requests.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text
            },
            timeout=10
        )
    except Exception as e:
        print("SEND ERROR:", e)


# ---------------- WEBHOOK ROUTE ----------------
@app.route("/", methods=["POST"])
def webhook():

    update = request.json
    print("UPDATE:", update)

    if not update:
        return "ok"

    message = update.get("message")
    if not message:
        return "ok"

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    print("USER:", text)

    # ---------------- COMMANDS ----------------
    if text == "/start":
        send_message(chat_id, "🤖 ربات وبهوک فعال شد!")

    elif text == "سلام":
        send_message(chat_id, "👋 سلام!")

    elif text == "خوبی":
        send_message(chat_id, "🙂 خوبم مرسی")

    else:
        send_message(chat_id, "❓ دستور ناشناخته")

    return "ok"


# ---------------- START SERVER ----------------
if __name__ == "__main__":
    print("🚀 Webhook Bot Started")

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
