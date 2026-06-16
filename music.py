import subprocess

def is_url(text):
    return text.startswith("http://") or text.startswith("https://")


def get_audio_from_url(url):
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "-f", "bestaudio",
                "-g",
                url
            ],
            capture_output=True,
            text=True,
            timeout=20   # ⛔ جلوگیری از گیر کردن
        )

        if result.returncode == 0:
            return result.stdout.strip()

        return None

    except Exception:
        return None


def download_video_from_url(url):
    filename = "video.mp4"

    try:
        subprocess.run([
            "yt-dlp",
            "-f", "bv+ba/b",
            "-o", filename,
            url
        ], timeout=60)

        return filename

    except Exception:
        return None
