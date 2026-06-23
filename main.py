import os
import time
import sqlite3
import requests
import numpy as np
from flask import Flask, jsonify
from sentence_transformers import SentenceTransformer
import fitz
import docx
from openai import OpenAI

# ================= CONFIG =================
BALE_TOKEN = os.getenv("BALE_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "586110315"))

BASE_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

# ================= MODEL (LAZY SAFE) =================
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# ================= DB =================
db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS memory(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
role TEXT,
text TEXT
)
""")

db.commit()

# ================= MEMORY STORE =================
docs = []
embeddings = []

# ================= FLASK =================
app = Flask(__name__)

@app.route("/api/status")
def status():
    return jsonify({"docs": len(docs)})

def run_api():
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ================= UTIL =================
def send(chat_id, text):
    requests.post(
        f"{BASE_URL}/sendMessage",
        json={"chat_id": chat_id, "text": text[:4000]}
    )

# ================= MEMORY =================
def save_memory(uid, role, text):
    cur.execute(
        "INSERT INTO memory(user_id,role,text) VALUES(?,?,?)",
        (uid, role, text[:2000])
    )
    db.commit()

def get_memory(uid):
    cur.execute("""
        SELECT role,text FROM memory
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
    """, (uid,))
    return cur.fetchall()[::-1]

# ================= EMBEDDING =================
def embed(text):
    return embed_model.encode(text)

def add_doc(text):
    docs.append(text)
    embeddings.append(embed(text))

# ================= PDF / DOCX =================
def load_pdf(path):
    doc = fitz.open(path)
    for page in doc:
        add_doc(page.get_text())

def load_docx(path):
    d = docx.Document(path)
    text = "\n".join([p.text for p in d.paragraphs])
    add_doc(text)

# ================= COSINE SEARCH =================
def search(query, top_k=5):
    if len(docs) == 0:
        return []

    q = embed(query)

    scores = []

    for i, emb in enumerate(embeddings):
        sim = np.dot(q, emb) / (np.linalg.norm(q) * np.linalg.norm(emb))
        scores.append((sim, docs[i]))

    scores.sort(reverse=True, key=lambda x: x[0])

    return [t for _, t in scores[:top_k]]

# ================= WEB RAG =================
def web_search(q):
    try:
        r = requests.get(f"https://duckduckgo.com/html/?q={q}", timeout=10)
        return [r.text[:1500]]
    except:
        return []

def add_web(q):
    for r in web_search(q):
        add_doc(r)

# ================= AI CORE =================
def ask_ai(uid, text):

    if "?" in text:
        add_web(text)

    context = search(text)
    memory = get_memory(uid)

    messages = [{
        "role": "system",
        "content": "تو یک AI هوشمند هستی. دقیق و تحلیلی جواب بده."
    }]

    for r, t in memory:
        messages.append({"role": r, "content": t})

    if context:
        messages.append({
            "role": "system",
            "content": "📚 Context:\n" + "\n".join(context)
        })

    messages.append({"role": "user", "content": text})

    res = client.chat.completions.create(
        model="Qwen/Qwen3-8B",
        messages=messages,
        max_tokens=500,
        temperature=0.6
    )

    answer = res.choices[0].message.content

    save_memory(uid, "user", text)
    save_memory(uid, "assistant", answer)

    return answer

# ================= BOT LOOP =================
print("🚀 LIGHT RAG BOT STARTED")

import threading
threading.Thread(target=run_api).start()

offset = 0

while True:
    try:
        data = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": offset, "timeout": 30}
        ).json()

        for upd in data.get("result", []):

            offset = upd["update_id"] + 1

            if "message" not in upd:
                continue

            msg = upd["message"]
            uid = msg["from"]["id"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "").strip()

            if not text:
                continue

            if text == "/start":
                send(chat_id, "🤖 AI آماده است (Light RAG Mode)")
                continue

            try:
                answer = ask_ai(uid, text)
                send(chat_id, answer)
            except Exception as e:
                send(chat_id, "خطا در پردازش")

    except Exception as e:
        print("ERR:", e)
        time.sleep(3)
