import requests
import time

from music import search_music, download_video, get_stream
from ai import recommend

TOKEN = "1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c"
BASE = f"https://tapi.bale.ai/bot{TOKEN}"

last_update = 0


# ---------- SEND TEXT ----------
def send(chat_id, text, reply=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }

    if reply:
        data["reply_markup"] = reply

    requests.post(BASE + "/sendMessage", json=data)


# ---------- SEND AUDIO ----------
def send_audio(chat_id, url):
    requests.post(BASE + "/sendAudio", data={
        "chat_id": chat_id,
        "audio": url
    })


# ---------- SEND VIDEO ----------
def send_video(chat_id, file_path):
    url = BASE + "/sendVideo"

    with open(file_path, "rb") as f:
        requests.post(url, data={
            "chat_id": chat_id
        }, files={
            "video": f
        })


# ---------- KEYBOARD ----------
def keyboard(title, url):
    return {
        "inline_keyboard": [
            [
                {"text": "▶️ Play", "url": url},
                {"text": "🔊 Stream", "callback_data": f"stream|{url}"}
            ],
            [
                {"text": "❤️ Like", "callback_data": f"like|{title}|{url}"},
                {"text": "🎯 AI", "callback_data": "ai"}
            ]
        ]
    }


# ---------- HANDLE SONG ----------
def handle_song(chat_id, user_id, text):
    result = search_music(text)

    # 🎵 AUDIO MODE
    if result:
        send(chat_id, f"🎵 {result['title']}", keyboard(result["title"], result["url"]))
        return

    # 🎬 VIDEO FALLBACK
    send(chat_id, "🎬 آهنگ پیدا نشد، در حال دانلود ویدیو...")

    video = download_video(text)
    send_video(chat_id, video)


# ---------- CALLBACK ----------
def handle_callback(chat_id, user_id, data):
    parts = data.split("|")

    if parts[0] == "stream":
        stream = get_stream(parts[1])
        send_audio(chat_id, stream)

    elif parts[0] == "ai":
        song = recommend(user_id)
        send(chat_id, f"🤖 {song['title']}", keyboard(song["title"], song["url"]))


# ---------- GET UPDATES ----------
def get_updates():
    global last_update

    res = requests.get(
        f"{BASE}/getUpdates?offset={last_update + 1}"
    ).json()

    for u in res.get("result", []):
        last_update = u["update_id"]

        # MESSAGE
        if "message" in u:
            msg = u["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")
            user_id = str(chat_id)

            if text.startswith("/start"):
                send(chat_id, "🎧 Music Bot Ready!")
            else:
                handle_song(chat_id, user_id, text)

        # CALLBACK
        elif "callback_query" in u:
            cb = u["callback_query"]
            chat_id = cb["message"]["chat"]["id"]
            user_id = str(chat_id)
            data = cb["data"]

            handle_callback(chat_id, user_id, data)


# ---------- RUN ----------
print("Bot is running...")

while True:
    try:
        get_updates()
        time.sleep(1)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(2)
