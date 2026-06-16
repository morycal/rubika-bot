import sqlite3

conn = sqlite3.connect("music.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS likes (
    user_id TEXT,
    title TEXT,
    url TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS history (
    user_id TEXT,
    title TEXT,
    url TEXT
)
""")

conn.commit()


def add_like(user_id, title, url):
    c.execute("INSERT INTO likes VALUES (?, ?, ?)", (user_id, title, url))
    conn.commit()


def get_likes(user_id):
    c.execute("SELECT title, url FROM likes WHERE user_id=?", (user_id,))
    return c.fetchall()
