"""
Authentication routes: signup, signin, forgot-password, verify-otp, reset-password, delete-account
"""

import os
import random
import string
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

from config import Config
from db import get_db

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
bcrypt = Bcrypt()


# ────────────────────────────────────────────────────────────
# POST /api/auth/signup
# ────────────────────────────────────────────────────────────
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    if not Config.is_valid_email(email):
        return jsonify({
            "error": "Invalid email domain. Please use a valid email provider (e.g. Gmail, Yahoo, Outlook, iCloud)."
        }), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
            (email, pw_hash),
        )
        conn.commit()
        user_id = cursor.lastrowid
    except Exception as e:
        conn.rollback()
        if "Duplicate entry" in str(e):
            return jsonify({"error": "An account with this email already exists."}), 409
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    token = create_access_token(identity=str(user_id))

    # Create welcome notification
    _create_notification(
        user_id,
        icon="sparkles",
        icon_color="#A78BFA",
        icon_bg="#2D1B69",
        title="Welcome to NutriFit!",
        body="Your personalized nutrition journey starts now. Set up your profile to get started.",
    )

    return jsonify({
        "message": "Account created successfully.",
        "token": token,
        "user_id": user_id,
    }), 201


# ────────────────────────────────────────────────────────────
# POST /api/auth/signin
# ────────────────────────────────────────────────────────────
@auth_bp.route("/signin", methods=["POST"])
def signin():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    if not Config.is_valid_email(email):
        return jsonify({
            "error": "Invalid email domain. Please use a valid email provider (e.g. Gmail, Yahoo, Outlook, iCloud)."
        }), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return jsonify({"error": "No account found with this email."}), 404

    if not bcrypt.check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid password."}), 401

    token = create_access_token(identity=str(user["id"]))

    return jsonify({
        "message": "Signed in successfully.",
        "token": token,
        "user": _user_to_dict(user),
    }), 200


# ────────────────────────────────────────────────────────────
# POST /api/auth/forgot-password
# ────────────────────────────────────────────────────────────
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({"error": "Email is required."}), 400

    if not Config.is_valid_email(email):
        return jsonify({"error": "Invalid email domain."}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        return jsonify({"error": "No account found with this email."}), 404

    # Generate 6-digit OTP
    code = "".join(random.choices(string.digits, k=6))
    expires_at = datetime.now() + timedelta(minutes=10)

    cursor.execute(
        "INSERT INTO otp_codes (email, code, expires_at) VALUES (%s, %s, %s)",
        (email, code, expires_at),
    )
    conn.commit()
    cursor.close()
    conn.close()

    # Send email
    try:
        brevo_key = os.environ.get("BREVO_API_KEY")
        if brevo_key:
            import requests
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {
                "accept": "application/json",
                "api-key": brevo_key,
                "content-type": "application/json"
            }
            payload = {
                "sender": {"email": Config.SMTP_EMAIL, "name": "NutriFit"},
                "to": [{"email": email}],
                "subject": "NutriFit Password Reset Code",
                "textContent": f"Your NutriFit verification code is: {code}\nThis code expires in 10 minutes."
            }
            res = requests.post(url, json=payload, headers=headers)
            if not res.ok:
                print(f"Brevo API error: {res.text}")
                return jsonify({"error": "Failed to send verification email via API. Please try again later."}), 500
        else:
            msg = EmailMessage()
            msg.set_content(f"Your NutriFit verification code is: {code}\nThis code expires in 10 minutes.")
            msg["Subject"] = "NutriFit Password Reset Code"
            msg["From"] = Config.SMTP_EMAIL
            msg["To"] = email

            server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT, timeout=10)
            server.starttls()
            server.login(Config.SMTP_EMAIL, Config.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")
        return jsonify({"error": f"Debug error: {str(e)}"}), 500

    return jsonify({
        "message": "Verification code sent to your email.",
    }), 200


# ────────────────────────────────────────────────────────────
# POST /api/auth/verify-otp
# ────────────────────────────────────────────────────────────
@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    code = (data.get("code") or "").strip()

    if not email or not code:
        return jsonify({"error": "Email and OTP code are required."}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT * FROM otp_codes
           WHERE email = %s AND code = %s AND used = 0
           ORDER BY created_at DESC LIMIT 1""",
        (email, code),
    )
    otp = cursor.fetchone()

    if not otp:
        cursor.close()
        conn.close()
        return jsonify({"error": "Invalid verification code."}), 400

    if otp["expires_at"] < datetime.now():
        cursor.close()
        conn.close()
        return jsonify({"error": "Verification code has expired. Please request a new one."}), 400

    # Mark as used
    cursor.execute("UPDATE otp_codes SET used = 1 WHERE id = %s", (otp["id"],))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "OTP verified successfully.", "verified": True}), 200


# ────────────────────────────────────────────────────────────
# POST /api/auth/reset-password
# ────────────────────────────────────────────────────────────
@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    new_password = data.get("new_password") or ""

    if not email or not new_password:
        return jsonify({"error": "Email and new password are required."}), 400

    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    pw_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password_hash = %s WHERE email = %s",
        (pw_hash, email),
    )
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()

    if affected == 0:
        return jsonify({"error": "No account found with this email."}), 404

    return jsonify({"message": "Password reset successfully."}), 200


# ────────────────────────────────────────────────────────────
# DELETE /api/auth/delete-account
# ────────────────────────────────────────────────────────────
@auth_bp.route("/delete-account", methods=["DELETE"])
@jwt_required()
def delete_account():
    user_id = int(get_jwt_identity())

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM meal_plans WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM intake_logs WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM chat_messages WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM notifications WHERE user_id = %s", (user_id,))
    
    # Finally delete the user
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Account and all data deleted permanently."}), 200


# ────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────
def _user_to_dict(row: dict) -> dict:
    return {
        "id": row["id"],
        "email": row["email"],
        "full_name": row.get("full_name", ""),
        "phone": row.get("phone", ""),
        "gender": row.get("gender", "Male"),
        "age": row.get("age", 25),
        "height_cm": row.get("height_cm", 170),
        "weight_kg": row.get("weight_kg", 70),
        "diet": row.get("diet", "pureVegetarian"),
        "conditions": row.get("conditions", ""),
        "fasting_glucose": row.get("fasting_glucose", 110),
        "carb_limit": row.get("carb_limit", "moderate"),
        "healthkit_enabled": bool(row.get("healthkit_enabled", 1)),
    }


def _create_notification(user_id, icon, icon_color, icon_bg, title, body):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO notifications
               (user_id, icon, icon_color, icon_bg, title, body)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (user_id, icon, icon_color, icon_bg, title, body),
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        pass
