"""
Coach AI routes: proxy to OpenRouter, persist chat history.
"""

from datetime import datetime

import requests as http_requests
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from config import Config
from db import get_db

coach_bp = Blueprint("coach", __name__, url_prefix="/api/coach")


# ────────────────────────────────────────────────────────────
# POST /api/coach/chat
# ────────────────────────────────────────────────────────────
@coach_bp.route("/chat", methods=["POST"])
@jwt_required()
def chat():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Message is required."}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Get user profile for context
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        conn.close()
        return jsonify({"error": "User not found."}), 404

    # Save user message
    cursor.execute(
        "INSERT INTO chat_messages (user_id, role, content) VALUES (%s, %s, %s)",
        (user_id, "user", user_message),
    )
    conn.commit()

    # Get recent chat history for context
    cursor.execute(
        """SELECT role, content FROM chat_messages
           WHERE user_id = %s
           ORDER BY created_at DESC LIMIT 10""",
        (user_id,),
    )
    recent = list(reversed(cursor.fetchall()))
    cursor.close()

    # Build system prompt
    name = user.get("full_name") or "Friend"
    gender = user.get("gender", "Male")
    age = user.get("age", 25)
    height_cm = user.get("height_cm", 170)
    weight_kg = user.get("weight_kg", 70)
    diet = user.get("diet", "pureVegetarian")
    conditions = user.get("conditions", "None")
    fasting_glucose = user.get("fasting_glucose", 0)
    carb_limit = user.get("carb_limit", "moderate")

    # Calculate BMR & TDEE
    if gender.lower() == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    elif gender.lower() == "female":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 80
    daily_goal = bmr * 1.375

    # Get today's intake
    today_str = datetime.now().strftime("%Y-%m-%d")
    cur2 = conn.cursor(dictionary=True)
    cur2.execute(
        """SELECT COALESCE(SUM(calories), 0) AS eaten
           FROM intake_logs
           WHERE user_id = %s AND log_date = %s""",
        (user_id, today_str),
    )
    eaten_row = cur2.fetchone()
    eaten = int(eaten_row["eaten"]) if eaten_row else 0
    cur2.close()
    conn.close()

    system_prompt = f"""You are NutriFit AI, a highly specialized, empathetic personal nutrition coach and fitness advisor.
Your goal is to answer fitness and nutrition questions based on the user's profile and calorie stats.

User Profile:
- Name: {name}
- Gender: {gender}
- Age: {age} years old
- Height: {height_cm} cm
- Weight: {weight_kg} kg
- Diet style: {diet}
- Health conditions: {conditions if conditions else 'None'}
- Fasting Glucose: {f'{fasting_glucose} mg/dL' if fasting_glucose > 0 else 'Not measured'}
- Carb Limit style: {carb_limit}

Today's Nutrition Stats:
- Target daily goal: {int(daily_goal)} kcal
- Calories eaten today: {eaten} kcal
- Calories remaining: {max(int(daily_goal) - eaten, 0)} kcal

Always address the user by their name ({name}) if appropriate. Keep your response concise, actionable, and formatted nicely (use short paragraphs and lists if needed). Avoid generic filler text."""

    # Build messages for OpenRouter
    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in recent:
        api_messages.append({
            "role": msg["role"],
            "content": msg["content"],
        })

    # Call OpenRouter
    try:
        resp = http_requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://nutrifit.ai",
                "X-Title": "NutriFit",
            },
            json={
                "model": Config.OPENROUTER_MODEL,
                "max_tokens": 500,
                "messages": api_messages,
            },
            timeout=30,
        )
        resp_json = resp.json()

        if "choices" in resp_json and resp_json["choices"]:
            ai_content = resp_json["choices"][0]["message"]["content"]
        elif "error" in resp_json:
            ai_content = "Coach is temporarily unavailable. Please try again shortly."
        else:
            ai_content = "Oops, something went wrong while processing the coach response."

    except Exception as e:
        ai_content = "Sorry, I couldn't reach the coaching service. Please check your internet connection."

    # Save assistant message
    conn2 = get_db()
    cur3 = conn2.cursor()
    cur3.execute(
        "INSERT INTO chat_messages (user_id, role, content) VALUES (%s, %s, %s)",
        (user_id, "assistant", ai_content),
    )
    conn2.commit()
    cur3.close()
    conn2.close()

    return jsonify({
        "reply": ai_content,
        "timestamp": datetime.now().isoformat(),
    }), 200


# ────────────────────────────────────────────────────────────
# GET /api/coach/history
# ────────────────────────────────────────────────────────────
@coach_bp.route("/history", methods=["GET"])
@jwt_required()
def get_history():
    user_id = int(get_jwt_identity())
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT id, role, content, created_at
           FROM chat_messages
           WHERE user_id = %s
           ORDER BY created_at ASC
           LIMIT %s OFFSET %s""",
        (user_id, limit, offset),
    )
    messages = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(*) AS total FROM chat_messages WHERE user_id = %s",
        (user_id,),
    )
    total = cursor.fetchone()["total"]
    cursor.close()
    conn.close()

    result = []
    for m in messages:
        result.append({
            "id": m["id"],
            "role": m["role"],
            "content": m["content"],
            "timestamp": m["created_at"].isoformat() if isinstance(m["created_at"], datetime) else str(m["created_at"]),
        })

    return jsonify({
        "messages": result,
        "total": total,
    }), 200


# ────────────────────────────────────────────────────────────
# DELETE /api/coach/history
# ────────────────────────────────────────────────────────────
@coach_bp.route("/history", methods=["DELETE"])
@jwt_required()
def clear_history():
    user_id = int(get_jwt_identity())

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages WHERE user_id = %s", (user_id,))
    conn.commit()
    deleted = cursor.rowcount
    cursor.close()
    conn.close()

    return jsonify({
        "message": f"Cleared {deleted} messages.",
    }), 200
