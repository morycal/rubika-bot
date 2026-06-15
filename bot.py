import os
import psycopg2
import requests
from flask import Flask, request, render_template, redirect, session

app = Flask(__name__)
app.secret_key = "CHANGE_ME"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "1234")


# ---------------- DB ----------------
def db():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        user_id TEXT,
        full_name TEXT,
        phone TEXT,
        insurance_type TEXT,
        description TEXT,
        status TEXT DEFAULT 'NEW',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    cur.close()
    conn.close()


init_db()


# ---------------- BOT ----------------
def send(chat_id, text):
    url = f"https://tapi.bale.ai/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})


@app.route("/", methods=["POST"])
def webhook():

    data = request.json
    if "message" not in data:
        return "ok"

    msg = data["message"]
    chat_id = str(msg["chat"]["id"])
    text = msg.get("text", "")

    # ثبت سریع سفارش (MVP هوشمند)
    send(chat_id, "✅ سفارش شما ثبت شد. کارشناسان به زودی تماس می‌گیرند.")

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO orders(user_id, full_name, phone, insurance_type, description)
        VALUES(%s,%s,%s,%s,%s)
    """, (
        chat_id,
        "نامشخص",
        "نامشخص",
        "نامشخص",
        text
    ))

    conn.commit()
    cur.close()
    conn.close()

    return "ok"


# ---------------- ADMIN LOGIN ----------------
@app.route("/admin", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        if request.form["username"] == ADMIN_USER and request.form["password"] == ADMIN_PASS:
            session["admin"] = True
            return redirect("/dashboard")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():

    if not session.get("admin"):
        return redirect("/admin")

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM orders")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders WHERE status='NEW'")
    new = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders WHERE status='DONE'")
    done = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template(
        "dashboard.html",
        orders=orders,
        total=total,
        new=new,
        done=done
    )


# ---------------- UPDATE STATUS ----------------
@app.route("/update/<int:oid>/<status>")
def update(oid, status):

    if not session.get("admin"):
        return redirect("/admin")

    conn = db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE orders SET status=%s WHERE id=%s",
        (status, oid)
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/dashboard")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
