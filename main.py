import os
import time
import requests
import sqlite3

# ================= CONFIG =================
BALE_TOKEN = os.getenv("BALE_TOKEN")

if not BALE_TOKEN:
    raise Exception("❌ BALE_TOKEN is not set!")

BASE_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

print("🚀 BOT STARTING...")

# ================= DELETE WEBHOOK (IMPORTANT FIX) =================
try:
    requests.get(f"{BASE_URL}/deleteWebhook")
    print("🧹 Webhook deleted (safe mode)")
except:
    pass

# ================= DB =================
db = sqlite3.connect("mori.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
created_at INTEGER
)
""")
db.commit()

# ================= SEND =================
def send(chat_id, text):
    try:
        requests.post(
            f"{BASE_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text[:4000]}
        )
    except Exception as e:
        print("SEND ERROR:", e)

def send_image(chat_id, img):
    try:
        requests.post(
            f"{BASE_URL}/sendPhoto",
            data={"chat_id": chat_id},
            files={"photo": ("img.png", img)}
        )
    except Exception as e:
        print("IMG ERROR:", e)

# ================= AI IMAGE (HUGGINGFACE) =================
HF_TOKEN = os.getenv("HF_TOKEN")

SD_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"

def generate_image(prompt):
    try:
        url = f"https://api-inference.huggingface.co/models/{SD_MODEL}"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}

        r = requests.post(url, headers=headers, json={"inputs": prompt})

        if r.status_code != 200:
            print("HF ERROR:", r.text)
            return None

        return r.content

    except Exception as e:
        print("GEN ERROR:", e)
        return None

# ================= PROMPT BOOST =================
def enhance(prompt):
    return f"{prompt}, ultra detailed, cinematic lighting, 8k, masterpiece"

# ================= MIDJOURNEY =================
def handle_mj(chat_id, uid, text):
    if not text.startswith("/mj"):
        return False

    prompt = text.replace("/mj", "").strip()

    if not prompt:
        send(chat_id, "❌ پرامپت خالیه")
        return True

    send(chat_id, "⏳ در حال ساخت تصویر...")

    final_prompt = enhance(prompt)

    img = generate_image(final_prompt)

    if not img:
        send(chat_id, "❌ خطا در ساخت تصویر")
        return True

    send_image(chat_id, img)

    send(chat_id, "✅ تمام شد")

    return True

# ================= MAIN LOOP =================
offset = 0

print("🎨 MORI MIDJOURNEY RUNNING")

while True:
    try:
        r = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": offset, "timeout": 20}
        )

        data = r.json()

        print("DEBUG:", data)  # مهم برای فهمیدن مشکل

        for upd in data.get("result", []):
            offset = upd["update_id"] + 1

            if "message" not in upd:
                continue

            msg = upd["message"]
            chat_id = msg["chat"]["id"]
            uid = msg["from"]["id"]
            text = msg.get("text", "")

            if not text:
                continue

            print("MSG:", text)

            # /start
            if text == "/start":
                send(chat_id, "👋 MORI MIDJOURNEY READY\nUse /mj prompt")
                continue

            # MJ handler
            if handle_mj(chat_id, uid, text):
                continue

    except Exception as e:
        print("CRASH:", e)
        time.sleep(3)
