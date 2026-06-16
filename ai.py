import random
from music import search_music

def recommend(user_id, text=""):
    queries = [
        "top songs 2026",
        "lofi music",
        "sad songs",
        "party hits"
    ]

    return search_music(random.choice(queries))
