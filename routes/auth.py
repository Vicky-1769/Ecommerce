
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from flask_mail import Message
from flask_dance.contrib.google import google
from extensions import mail, mongo
import random
from threading import Thread

auth_bp = Blueprint("auth", __name__)

# -----------------------------
# ASYNC EMAIL SENDER
# -----------------------------
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


# -----------------------------
# LOGIN ROUTE (OTP SYSTEM)
# -----------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")

        # Admin Login Shortcut
        if email == "admin@devstore.com":
            session["user"] = email
            flash("Admin logged in successfully!", "success")
            return redirect(url_for("admin.admin"))

        # Generate OTP
        otp = str(random.randint(100000, 999999))

        session["otp"] = otp
        session["email"] = email

        # Email Message
        msg = Message(
            "Your OTP Code",
            sender=current_app.config.get("MAIL_USERNAME"),
            recipients=[email]
        )

        msg.body = f"""
Hello,

Your OTP for login is: {otp}

If you did not request this, please ignore.

DevStore Security
"""

        try:
            # Note: Render Free tier blocks outbound SMTP ports (25, 465, 587).
            # The background thread prevents the 500 crash, but the email will silently fail.
            Thread(
                target=send_async_email,
                args=(current_app._get_current_object(), msg)
            ).start()

            # For testing/demo purposes, we show the OTP directly because Render Free will block the real email.
            flash("OTP process started! Note: Render Free tier blocks Gmail SMTP.", "info")
            flash(f"Since this is deployed on a free Render tier, your OTP is: {otp} (Testing Fallback)", "warning")

        except Exception as e:
            print("Email Error:", e)
            flash("Email failed. Use OTP 123456 for testing.", "danger")
            session["otp"] = "123456"

        return redirect(url_for("auth.verify"))

    return render_template("login.html")


# -----------------------------
# OTP VERIFICATION
# -----------------------------
@auth_bp.route("/verify", methods=["GET", "POST"])
def verify():

    if request.method == "POST":

        user_otp = request.form.get("otp")

        if user_otp == session.get("otp"):

            email = session.get("email")

            session["user"] = email

            # Save user in database if not exists
            if not mongo.db.users.find_one({"email": email}):
                mongo.db.users.insert_one({"email": email})

            flash("Login successful!", "success")

            return redirect(url_for("main.shop"))

        else:
            flash("Invalid OTP", "danger")

    return render_template("verify.html")


# -----------------------------
# GOOGLE LOGIN
# -----------------------------
@auth_bp.route("/google_login")
def google_login():

    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")

    if resp.ok:

        user_info = resp.json()

        email = user_info["email"]

        session["user"] = email

        if not mongo.db.users.find_one({"email": email}):
            mongo.db.users.insert_one({"email": email})

        flash("Logged in with Google!", "success")

    return redirect(url_for("main.shop"))


# -----------------------------
# LOGOUT
# -----------------------------
@auth_bp.route("/logout")
def logout():

    session.clear()

    flash("Logged out successfully.", "success")

    return redirect(url_for("main.shop"))
