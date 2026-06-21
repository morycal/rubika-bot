import os
import time
import requests
from openai import OpenAI

BALE_TOKEN = os.getenv("1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c")
HF_TOKEN = os.getenv("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")

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

BASE_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

def ask_ai(text):
    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen3-8B",
            messages=[
                {
                    "role": "system",
                    "content": "تو یک دستیار فارسی‌زبان مفید هستی."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            max_tokens=500
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"خطا: {e}"

def send_message(chat_id, text):
    requests.post(
        f"{BASE_URL}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text[:4000]
        },
        timeout=30
    )

offset = 0

print("Bot Started...")

while True:
    try:
        updates = requests.get(
            f"{BASE_URL}/getUpdates",
            params={
                "offset": offset,
                "timeout": 30
            },
            timeout=35
        ).json()

        for update in updates.get("result", []):

            offset = update["update_id"] + 1

            if "message" not in update:
                continue

            message = update["message"]

            chat_id = message["chat"]["id"]
            text = message.get("text", "")

            if text == "/start":
                send_message(
                    chat_id,
                    "سلام 👋\nمن بات هوش مصنوعی هستم.\nهر سوالی داری بپرس."
                )
                continue

            if not text:
                continue

            answer = ask_ai(text)

            send_message(chat_id, answer)

    except Exception as e:
        print(e)
        time.sleep(5)
