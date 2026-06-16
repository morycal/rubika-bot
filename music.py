import subprocess

def search_music(query):
    result = subprocess.getoutput(
        f'yt-dlp "ytsearch1:{query}" --get-title --get-url'
    ).split("\n")

    if len(result) >= 2:
        return {
            "type": "audio",
            "title": result[0],
            "url": result[1]
        }

    return None


def download_video(query):
    filename = "video.mp4"

    subprocess.call([
        "yt-dlp",
        "-f", "mp4",
        "-o", filename,
        f"ytsearch1:{query}"
    ])

    return filename


def get_stream(url):
    return subprocess.getoutput(
        f'yt-dlp -f bestaudio -g "{url}"'
    ).strip()
