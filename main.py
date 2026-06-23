import os
import time
import sqlite3
import requests
import threading
from flask import Flask
from openai import OpenAI

# ================= CONFIG =================
BALE_TOKEN = os.getenv("BALE_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "586110315"))

BASE_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

# ================= DB =================
db = sqlite3.connect("mori_mj.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
created_at INTEGER DEFAULT 0
)
""")

db.commit()

# ================= MEMORY =================
user_images = {}

# ================= SEND =================
def send(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text[:4000]}
    if reply_markup:
        data["reply_markup"] = reply_markup

    requests.post(f"{BASE_URL}/sendMessage", json=data)

def send_image(chat_id, img):
    requests.post(
        f"{BASE_URL}/sendPhoto",
        data={"chat_id": chat_id},
        files={"photo": ("img.png", img)}
    )

# ================= MODEL =================
SD_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"

def generate_4_images(prompt):
    url = f"https://api-inference.huggingface.co/models/{SD_MODEL}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}

    images = []

    for _ in range(4):
        r = requests.post(url, headers=headers, json={"inputs": prompt})
        if r.status_code == 200:
            images.append(r.content)

    return images

# ================= PROMPT BOOST =================
def enhance_prompt(prompt):
    return f"{prompt}, ultra detailed, cinematic lighting, 8k, masterpiece, high quality"

# ================= MIDJOURNEY MENU =================
def mj_menu(chat_id):
    send(
        chat_id,
        "🎨 MORI MIDJOURNEY\n\nیک پرامپت بفرست:\n/mj prompt",
        reply_markup={
            "inline_keyboard": [
                [{"text": "ℹ️ راهنما", "callback_data": "mj_help"}]
            ]
        }
    )

# ================= HANDLER =================
def handle_midjourney(uid, chat_id, text):

    if text.startswith("/mj"):
        prompt = text.replace("/mj", "").strip()

        if not prompt:
            send(chat_id, "❌ لطفاً پرامپت بنویس")
            return True

        final_prompt = enhance_prompt(prompt)

        send(chat_id, "⏳ در حال ساخت 4 تصویر...")

        images = generate_4_images(final_prompt)

        if not images:
            send(chat_id, "❌ خطا در ساخت تصویر")
            return True

        user_images[uid] = images

        for img in images:
            send_image(chat_id, img)

        send(
            chat_id,
            "⭐ یکی را انتخاب کن یا دوباره بساز",
            reply_markup={
                "inline_keyboard": [
                    [
                        {"text": "⭐ 1", "callback_data": "mj_1"},
                        {"text": "⭐ 2", "callback_data": "mj_2"}
                    ],
                    [
                        {"text": "⭐ 3", "callback_data": "mj_3"},
                        {"text": "⭐ 4", "callback_data": "mj_4"}
                    ],
                    [
                        {"text": "🔁 دوباره", "callback_data": "mj_reroll"}
                    ]
                ]
            }
        )

        return True

    return False

# ================= CALLBACK =================
def handle_callback(data, chat_id, uid):

    if data == "mj_help":
        send(chat_id, "🎨 دستور:\n/mj a futuristic city")
        return True

    if data == "mj_reroll":
        send(chat_id, "🔁 دوباره /mj بفرست")
        return True

    if data.startswith("mj_") and uid in user_images:
        idx = int(data.split("_")[1]) - 1

        if 0 <= idx < len(user_images[uid]):
            send_image(chat_id, user_images[uid][idx])

        return True

    return False

# ================= BOT LOOP =================
offset = 0

print("🎨 MORI MIDJOURNEY RUNNING")

while True:
    try:
        res = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": offset, "timeout": 30}
        ).json()

        for upd in res.get("result", []):
            offset = upd["update_id"] + 1

            # CALLBACK
            if "callback_query" in upd:
                cq = upd["callback_query"]

                handle_callback(
                    cq["data"],
                    cq["message"]["chat"]["id"],
                    cq["from"]["id"]
                )
                continue

            if "message" not in upd:
                continue

            msg = upd["message"]
            uid = msg["from"]["id"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")

            if not text:
                continue

            # MENU
            if text == "/mjmenu":
                mj_menu(chat_id)
                continue

            # MIDJOURNEY
            if handle_midjourney(uid, chat_id, text):
                continue

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)
