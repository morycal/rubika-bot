import requests
import time

from music import search_music, get_stream
from db import add_like
from ai import recommend

TOKEN = "1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c"
BASE = f"https://tapi.bale.ai/bot{TOKEN}"

last_update = 0


def send(chat_id, text, reply=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }
    if reply:
        data["reply_markup"] = reply

    requests.post(BASE + "/sendMessage", json=data)


def send_audio(chat_id, url):
    requests.post(BASE + "/sendAudio", data={
        "chat_id": chat_id,
        "audio": url
    })


def keyboard(title, url):
    return {
        "inline_keyboard": [
            [
                {"text": "▶️ Play", "url": url},
                {"text": "🔊 Stream", "callback_data": f"stream|{url}"}
            ],
            [
                {"text": "⬇️ Download", "callback_data": f"dl|{url}"},
                {"text": "❤️ Like", "callback_data": f"like|{title}|{url}"}
            ],
            [
                {"text": "🎯 AI Recommend", "callback_data": "ai"}
            ]
        ]
    }


def handle_song(chat_id, user_id, text):
    songs = search_music(text)

    if not songs:
        send(chat_id, "❌ چیزی پیدا نشد")
        return

    for s in songs:
        send(chat_id, f"🎵 {s['title']}", keyboard(s["title"], s["url"]))


def handle_callback(chat_id, user_id, data):
    parts = data.split("|")

    if parts[0] == "like":
        title, url = parts[1], parts[2]
        add_like(user_id, title, url)
        send(chat_id, "❤️ ذخیره شد")

    elif parts[0] == "stream":
        stream_url = get_stream(parts[1])
        send_audio(chat_id, stream_url)

    elif parts[0] == "ai":
        songs = recommend(user_id, "mood")
        for s in songs:
            send(chat_id, f"🎧 {s['title']}", keyboard(s["title"], s["url"]))


def get_updates():
    global last_update

    res = requests.get(
        f"{BASE}/getUpdates?offset={last_update+1}"
    ).json()

    for u in res.get("result", []):
        last_update = u["update_id"]

        if "message" in u:
            msg = u["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")
            user_id = str(chat_id)

            if text.startswith("/start"):
                send(chat_id, "🎧 Welcome to Music AI Bot")
            else:
                handle_song(chat_id, user_id, text)

        elif "callback_query" in u:
            cb = u["callback_query"]
            chat_id = cb["message"]["chat"]["id"]
            user_id = str(chat_id)
            data = cb["data"]

            handle_callback(chat_id, user_id, data)


print("Bot running...")

while True:
    try:
        get_updates()
        time.sleep(1)
    except:
        time.sleep(2)
