import os
import time
import sqlite3
import requests
import numpy as np
import faiss
import fitz
import docx
from flask import Flask, jsonify
from sentence_transformers import SentenceTransformer, CrossEncoder
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

# ================= MODELS =================
embed_model = SentenceTransformer("all-MiniLM-L6-v2")
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")

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

# ================= VECTOR DB =================
dim = 384
index = faiss.IndexFlatL2(dim)

docs = []
graph = {}

# ================= FLASK =================
app = Flask(__name__)

@app.route("/api/status")
def status():
    return jsonify({"docs": len(docs)})

def run_api():
    app.run(host="0.0.0.0", port=5000)

# ================= UTIL =================
def send(chat_id, text):
    requests.post(f"{BASE_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text[:4000]
    })

# ================= MEMORY =================
def get_memory(uid):
    cur.execute("""
        SELECT role,text FROM memory
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 12
    """, (uid,))
    return cur.fetchall()[::-1]

def save_memory(uid, role, text):
    cur.execute("INSERT INTO memory(user_id,role,text) VALUES(?,?,?)",
                (uid, role, text[:2000]))
    db.commit()

# ================= INGESTION =================
def add_doc(text, topic="general"):
    emb = embed_model.encode([text])[0].astype("float32")
    index.add(np.array([emb]))
    docs.append(text)
    graph.setdefault(topic, []).append(text)

def load_pdf(path):
    doc = fitz.open(path)
    for page in doc:
        add_doc(page.get_text(), "pdf")

def load_docx(path):
    d = docx.Document(path)
    text = "\n".join([p.text for p in d.paragraphs])
    add_doc(text, "docx")

# ================= WEB RAG =================
def web_search(q):
    try:
        r = requests.get(f"https://duckduckgo.com/html/?q={q}", timeout=10)
        return [r.text[:2000]]
    except:
        return []

def add_web(q):
    for r in web_search(q):
        add_doc(r, "web")

# ================= RETRIEVE =================
def retrieve(q, k=8):
    if len(docs) == 0:
        return []

    q_emb = embed_model.encode([q])[0].astype("float32")
    D, I = index.search(np.array([q_emb]), k)

    candidates = [docs[i] for i in I[0] if i < len(docs)]

    if not candidates:
        return []

    scores = reranker.predict([[q, c] for c in candidates])

    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)

    return [r[0] for r in ranked[:5]]

# ================= GRAPH =================
def graph_ctx(q):
    out = []
    for k,v in graph.items():
        if k in q:
            out += v[:2]
    return out

# ================= AI =================
def ask_ai(uid, text):

    if "?" in text:
        add_web(text)

    context = retrieve(text)
    gctx = graph_ctx(text)
    memory = get_memory(uid)

    messages = [{
        "role":"system",
        "content":"""
تو یک AI بسیار پیشرفته هستی (GPT-4 level RAG).

قوانین:
- فقط از داده‌ها استفاده کن
- تحلیل عمیق بده
- اگر مطمئن نیستی بگو نمی‌دانم
"""
    }]

    for r,t in memory:
        messages.append({"role":r,"content":t})

    if context:
        messages.append({"role":"system","content":"📚 Context:\n"+"\n".join(context)})

    if gctx:
        messages.append({"role":"system","content":"🗂 Graph:\n"+"\n".join(gctx)})

    messages.append({"role":"user","content":text})

    stream = client.chat.completions.create(
        model="Qwen/Qwen3-8B",
        messages=messages,
        stream=True,
        max_tokens=500
    )

    out = ""

    for chunk in stream:
        if chunk.choices[0].delta.content:
            token = chunk.choices[0].delta.content
            out += token
            print(token, end="", flush=True)

    save_memory(uid, "user", text)
    save_memory(uid, "assistant", out)

    return out

# ================= BOT LOOP =================
print("BOT + RAG STARTED")

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
            text = msg.get("text","").strip()

            if not text:
                continue

            if text == "/start":
                send(chat_id, "🤖 RAG AI فعال شد")
                continue

            try:
                answer = ask_ai(uid, text)
                send(chat_id, answer)
            except Exception as e:
                send(chat_id, f"خطا: {e}")

    except Exception as e:
        print("ERR:", e)
        time.sleep(3)
