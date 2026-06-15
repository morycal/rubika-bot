from flask import Flask, render_template, request, redirect, session
from db import conn

app = Flask(__name__)
app.secret_key = "secret123"

ADMIN_USER = "admin"
ADMIN_PASS = "1234"


# ---------- LOGIN ----------
@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        if request.form["username"] == ADMIN_USER and request.form["password"] == ADMIN_PASS:
            session["admin"] = True
            return redirect("/dashboard")

    return render_template("login.html")


# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():

    if not session.get("admin"):
        return redirect("/")

    c = conn()
    cur = c.cursor()

    cur.execute("SELECT COUNT(*) FROM orders WHERE status='NEW'")
    new = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders")
    total = cur.fetchone()[0]

    cur.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = cur.fetchall()

    return render_template("dashboard.html",
        new=new,
        total=total,
        orders=orders
    )


# ---------- UPDATE STATUS ----------
@app.route("/update/<int:oid>/<status>")
def update(oid, status):

    c = conn()
    cur = c.cursor()

    cur.execute("UPDATE orders SET status=%s WHERE id=%s", (status, oid))

    c.commit()
    cur.close()
    c.close()

    return redirect("/dashboard")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
