import subprocess

def is_url(text):
    return text.startswith("http://") or text.startswith("https://")


def search_music(query):
    result = subprocess.getoutput(
        f'yt-dlp "ytsearch1:{query}" --get-title --get-url'
    ).split("\n")

    if len(result) >= 2:
        return {
            "title": result[0],
            "url": result[1]
        }

    return None


def get_audio_from_url(url):
    result = subprocess.getoutput(
        f'yt-dlp -f bestaudio -g "{url}"'
    )
    return result.strip()


def download_video_from_url(url):
    filename = "video.mp4"

    subprocess.call([
        "yt-dlp",
        "-f", "bv+ba/b",
        "-o", filename,
        url
    ])

    return filename
