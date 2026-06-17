"""
Profile routes: get / update profile, health data, settings.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import uuid
from werkzeug.utils import secure_filename
from db import get_db

profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")


# ────────────────────────────────────────────────────────────
# GET /api/profile
# ────────────────────────────────────────────────────────────
@profile_bp.route("", methods=["GET"])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return jsonify({"error": "User not found."}), 404

    return jsonify({"user": _profile_dict(user)}), 200


# ────────────────────────────────────────────────────────────
# PUT /api/profile
# ────────────────────────────────────────────────────────────
@profile_bp.route("", methods=["PUT"])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    allowed = [
        "full_name", "phone", "gender", "age",
        "height_cm", "weight_kg", "email",
    ]
    sets = []
    vals = []
    for key in allowed:
        if key in data:
            sets.append(f"{key} = %s")
            vals.append(data[key])

    if not sets:
        return jsonify({"error": "No fields to update."}), 400

    vals.append(user_id)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE users SET {', '.join(sets)} WHERE id = %s",
        tuple(vals),
    )
    conn.commit()
    cursor.close()

    # Fetch updated profile
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    return jsonify({"message": "Profile updated.", "user": _profile_dict(user)}), 200


# ────────────────────────────────────────────────────────────
# PUT /api/profile/health
# ────────────────────────────────────────────────────────────
@profile_bp.route("/health", methods=["PUT"])
@jwt_required()
def update_health():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    allowed = ["conditions", "diet", "fasting_glucose", "carb_limit"]
    sets = []
    vals = []
    for key in allowed:
        if key in data:
            sets.append(f"{key} = %s")
            vals.append(data[key])

    if not sets:
        return jsonify({"error": "No health fields to update."}), 400

    vals.append(user_id)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE users SET {', '.join(sets)} WHERE id = %s",
        tuple(vals),
    )
    conn.commit()

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    return jsonify({"message": "Health data updated.", "user": _profile_dict(user)}), 200


# ────────────────────────────────────────────────────────────
# PUT /api/profile/settings
# ────────────────────────────────────────────────────────────
@profile_bp.route("/settings", methods=["PUT"])
@jwt_required()
def update_settings():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    sets = []
    vals = []

    if "healthkit_enabled" in data:
        sets.append("healthkit_enabled = %s")
        vals.append(1 if data["healthkit_enabled"] else 0)

    if not sets:
        return jsonify({"error": "No settings to update."}), 400

    vals.append(user_id)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE users SET {', '.join(sets)} WHERE id = %s",
        tuple(vals),
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Settings updated."}), 200


# ────────────────────────────────────────────────────────────
# POST /api/profile/photo
# ────────────────────────────────────────────────────────────
@profile_bp.route("/photo", methods=["POST"])
@jwt_required()
def upload_photo():
    user_id = int(get_jwt_identity())
    
    if "photo" not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files["photo"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
        
    if file:
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1]
        new_filename = f"user_{user_id}_{uuid.uuid4().hex[:8]}{ext}"
        
        uploads_dir = os.path.join(current_app.root_path, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        
        file_path = os.path.join(uploads_dir, new_filename)
        file.save(file_path)
        
        photo_url = f"/uploads/{new_filename}"
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET profile_photo = %s WHERE id = %s", (photo_url, user_id))
        conn.commit()
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return jsonify({"message": "Photo uploaded.", "user": _profile_dict(user)}), 200

# ────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────
def _profile_dict(row: dict) -> dict:
    return {
        "id": row["id"],
        "email": row.get("email", ""),
        "full_name": row.get("full_name", ""),
        "phone": row.get("phone", ""),
        "gender": row.get("gender", "Male"),
        "age": row.get("age", 25),
        "height_cm": row.get("height_cm", 170.0),
        "weight_kg": row.get("weight_kg", 70.0),
        "diet": row.get("diet", "pureVegetarian"),
        "conditions": row.get("conditions", ""),
        "fasting_glucose": row.get("fasting_glucose", 110.0),
        "carb_limit": row.get("carb_limit", "moderate"),
        "healthkit_enabled": bool(row.get("healthkit_enabled", 1)),
        "profile_photo": row.get("profile_photo"),
    }
