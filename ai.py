import subprocess

def search_music(query):
    result = subprocess.getoutput(
        f'yt-dlp "ytsearch3:{query}" --get-title --get-url'
    ).split("\n")

    songs = []
    for i in range(0, len(result)-1, 2):
        songs.append({
            "title": result[i],
            "url": result[i+1]
        })

    return songs


def get_stream(url):
    return subprocess.getoutput(
        f'yt-dlp -f bestaudio -g "{url}"'
    ).strip()
