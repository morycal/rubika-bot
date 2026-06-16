import random
from db import get_likes
from music import search_music


def detect_mood(text):
    text = text.lower()

    if "غم" in text or "sad" in text:
        return "sad"
    if "پارتی" in text or "party" in text:
        return "party"
    if "تمرکز" in text or "focus" in text:
        return "focus"

    return "normal"
    

def recommend(user_id, text=""):
    """
    AI recommendation engine (Spotify-like)
    """

    mood = detect_mood(text)

    if mood == "sad":
        return search_music("sad emotional songs playlist")

    if mood == "party":
        return search_music("party hits 2026")

    if mood == "focus":
        return search_music("lofi focus music")

    # اگر کاربر لایک دارد → پیشنهاد هوشمند
    likes = get_likes(user_id)

    if likes:
        seed = random.choice(likes)[0]
        return search_music(seed + " similar songs")

    # حالت پیش‌فرض
    return search_music("top trending music 2026")
