import os
import re
import time
import requests
from yt_dlp import YoutubeDL

BOT_TOKEN = os.getenv("BOT_TOKEN")
AUDD_TOKEN = os.getenv("AUDD_TOKEN")

offset = 0


def send(chat_id, text):
    requests.post(
        f"https://tapi.bale.ai/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text
        }
    )


def get_updates(offset):
    r = requests.get(
        f"https://tapi.bale.ai/bot{BOT_TOKEN}/getUpdates",
        params={"offset": offset}
    )

    return r.json().get("result", [])


def is_url(text):
    return bool(re.search(r'https?://', text))


def get_direct_audio_url(video_url):

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "format": "bestaudio"
    }

    with YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(video_url, download=False)

        if "url" in info:
            return info["url"]

        formats = info.get("formats", [])

        for f in reversed(formats):
            if f.get("acodec") != "none":
                return f["url"]

    return None


def recognize_song(audio_url):

    r = requests.post(
        "https://api.audd.io/",
        data={
            "api_token": AUDD_TOKEN,
            "url": audio_url,
            "return": "spotify,apple_music"
        },
        timeout=120
    )

    data = r.json()

    if not data.get("result"):
        return None

    return data["result"]


def format_result(song):

    title = song.get("title", "نامشخص")
    artist = song.get("artist", "نامشخص")
    album = song.get("album", "نامشخص")

    msg = f"""
🎵 آهنگ پیدا شد

🎶 {title}

🎤 {artist}

💿 {album}
"""

    spotify = song.get("spotify")

    if spotify:
        msg += f"\n🎧 Spotify:\n{spotify.get('external_urls',{}).get('spotify','')}"

    apple = song.get("apple_music")

    if apple:
        msg += f"\n\n🍎 Apple Music:\n{apple.get('url','')}"

    return msg


print("Music Finder Bot Started")


while True:

    try:

        updates = get_updates(offset)

        for update in updates:

            offset = update["update_id"] + 1

            if "message" not in update:
                continue

            msg = update["message"]

            chat_id = msg["chat"]["id"]

            text = msg.get("text", "")

            if text == "/start":

                send(
                    chat_id,
                    """🎵 ربات موسیقی‌یاب

لینک:
• YouTube
• Instagram Reel
• TikTok
• Aparat

را ارسال کنید."""
                )

                continue

            if not is_url(text):

                send(
                    chat_id,
                    "❌ لطفاً لینک ویدیو ارسال کنید."
                )

                continue

            send(
                chat_id,
                "🔍 در حال بررسی ویدیو..."
            )

            audio_url = get_direct_audio_url(text)

            if not audio_url:

                send(
                    chat_id,
                    "❌ خطا در دریافت صدا."
                )

                continue

            send(
                chat_id,
                "🎧 در حال تشخیص آهنگ..."
            )

            song = recognize_song(audio_url)

            if not song:

                send(
                    chat_id,
                    "❌ آهنگی پیدا نشد."
                )

                continue

            send(
                chat_id,
                format_result(song)
            )

    except Exception as e:
        print(e)

    time.sleep(2)
