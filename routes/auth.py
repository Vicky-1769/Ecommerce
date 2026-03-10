from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from flask_mail import Message
from flask_dance.contrib.google import google
import random
from extensions import mongo, mail

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        
        # Admin bypass for testing effortlessly without email
        if email == "admin@devstore.com":
            session["user"] = email
            flash("Admin logged in instantly.", "success")
            return redirect(url_for("admin.admin"))
            
        otp = str(random.randint(100000, 999999))
        session["otp"] = otp
        session["email"] = email

        msg = Message("Your OTP Code", sender=current_app.config.get("MAIL_USERNAME"), recipients=[email])
        msg.body = f"Your OTP is {otp}"
        try:
            from threading import Thread
from flask import current_app

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

Thread(
    target=send_async_email,
    args=(current_app._get_current_object(), msg)
).start()
            flash("OTP sent to your email! Please check.", "info")
        except Exception as e:
            flash(f"Error sending email. Use 123456 as a bypass for testing or fix SMTP.", "danger")
            session["otp"] = "123456" # fallback for dev
        return redirect(url_for("auth.verify"))

    return render_template("login.html")

@auth_bp.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "POST":
        user_otp = request.form["otp"]
        if user_otp == session.get("otp"):
            user = mongo.db.users.find_one({"email": session.get("email")})
            if not user:
                mongo.db.users.insert_one({"email": session.get("email")})
            session["user"] = session.get("email")
            flash("Logged in successfully!", "success")
            return redirect(url_for("main.shop"))
        else:
            flash("Invalid OTP. Try again.", "danger")

    return render_template("verify.html")

@auth_bp.route("/google_login")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if resp.ok:
        email = resp.json()["email"]
        
        user = mongo.db.users.find_one({"email": email})
        if not user:
            mongo.db.users.insert_one({"email": email})
            
        session["user"] = email
        flash("Logged in with Google successfully!", "success")
        return redirect(url_for("main.shop"))
    
    flash("Google login failed.", "danger")
    return redirect(url_for("auth.login"))

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("main.home"))
