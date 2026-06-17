"""
Intake logging routes: log a meal, get today's totals, get history.
"""

from datetime import date, datetime, timedelta

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db

intake_bp = Blueprint("intake", __name__, url_prefix="/api/intake")


# ────────────────────────────────────────────────────────────
# POST /api/intake/log
# ────────────────────────────────────────────────────────────
@intake_bp.route("/log", methods=["POST"])
@jwt_required()
def log_intake():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    meal_name = data.get("meal_name", "")
    calories = data.get("calories", 0)
    protein = data.get("protein", 0)
    carbs = data.get("carbs", 0)
    fat = data.get("fat", 0)
    portion_g = data.get("portion_g", 150)
    log_date = data.get("date", str(date.today()))

    try:
        d = datetime.strptime(log_date, "%Y-%m-%d").date()
    except ValueError:
        d = date.today()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO intake_logs
           (user_id, log_date, meal_name, calories, protein, carbs, fat, portion_g)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (user_id, d, meal_name, calories, protein, carbs, fat, portion_g),
    )
    conn.commit()
    log_id = cursor.lastrowid
    cursor.close()
    conn.close()

    return jsonify({
        "message": "Intake logged.",
        "log_id": log_id,
    }), 201


# ────────────────────────────────────────────────────────────
# GET /api/intake/today
# ────────────────────────────────────────────────────────────
@intake_bp.route("/today", methods=["GET"])
@jwt_required()
def today_intake():
    user_id = int(get_jwt_identity())
    today = date.today()

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT
               COALESCE(SUM(calories), 0) AS total_calories,
               COALESCE(SUM(protein), 0)  AS total_protein,
               COALESCE(SUM(carbs), 0)    AS total_carbs,
               COALESCE(SUM(fat), 0)      AS total_fat,
               COUNT(*)                   AS meal_count
           FROM intake_logs
           WHERE user_id = %s AND log_date = %s""",
        (user_id, today),
    )
    totals = cursor.fetchone()

    # Also get individual entries
    cursor.execute(
        """SELECT id, meal_name, calories, protein, carbs, fat, portion_g, logged_at
           FROM intake_logs
           WHERE user_id = %s AND log_date = %s
           ORDER BY logged_at DESC""",
        (user_id, today),
    )
    entries = cursor.fetchall()
    cursor.close()
    conn.close()

    # Convert timestamps to strings
    for e in entries:
        if isinstance(e.get("logged_at"), datetime):
            e["logged_at"] = e["logged_at"].isoformat()

    return jsonify({
        "date": str(today),
        "totals": {
            "calories": int(totals["total_calories"]),
            "protein": int(totals["total_protein"]),
            "carbs": int(totals["total_carbs"]),
            "fat": int(totals["total_fat"]),
            "meal_count": int(totals["meal_count"]),
        },
        "entries": entries,
    }), 200


# ────────────────────────────────────────────────────────────
# GET /api/intake/history
# ────────────────────────────────────────────────────────────
@intake_bp.route("/history", methods=["GET"])
@jwt_required()
def intake_history():
    user_id = int(get_jwt_identity())
    days = request.args.get("days", 7, type=int)
    start_date = date.today() - timedelta(days=days - 1)

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT
               log_date,
               SUM(calories) AS total_calories,
               SUM(protein)  AS total_protein,
               SUM(carbs)    AS total_carbs,
               SUM(fat)      AS total_fat,
               COUNT(*)      AS meal_count
           FROM intake_logs
           WHERE user_id = %s AND log_date >= %s
           GROUP BY log_date
           ORDER BY log_date DESC""",
        (user_id, start_date),
    )
    history = cursor.fetchall()
    cursor.close()
    conn.close()

    result = []
    for h in history:
        result.append({
            "date": str(h["log_date"]),
            "calories": int(h["total_calories"]),
            "protein": int(h["total_protein"]),
            "carbs": int(h["total_carbs"]),
            "fat": int(h["total_fat"]),
            "meal_count": int(h["meal_count"]),
        })

    return jsonify({"history": result}), 200
