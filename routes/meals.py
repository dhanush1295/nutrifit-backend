"""
Meal plan & food database routes.
Auto-generates a daily plan based on user conditions/diet, supports swap.
"""

import random
from datetime import date, datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db

# Import the EXTRA_FOODS from extra_foods.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from extra_foods import EXTRA_FOODS
except ImportError:
    EXTRA_FOODS = []

meals_bp = Blueprint("meals", __name__, url_prefix="/api/meals")

# ────────────────────────────────────────────────────────────
# POST /api/meals/seed
# ────────────────────────────────────────────────────────────
@meals_bp.route("/seed", methods=["POST"])
def seed_remote_foods():
    # Only insert if empty
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as c FROM foods")
    count = cursor.fetchone()[0]
    if count > 0:
        cursor.close()
        conn.close()
        return jsonify({"message": f"Database already has {count} foods."}), 200

    cursor.execute("DELETE FROM foods")
    conn.commit()

    inserted = 0
    for f in EXTRA_FOODS:
        try:
            cursor.execute(
                """INSERT INTO foods 
                   (name, emoji, calories, protein, carbs, fat, diet, avoid_for, safe_for, meal_times, subtitle, ingredients)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    f["name"], f["emoji"], f["calories"], f["protein"], f["carbs"], f["fat"],
                    f["diet"], f.get("avoid_for", ""), f.get("safe_for", ""), f.get("meal_times", ""),
                    f.get("subtitle", ""), f.get("ingredients", "")
                )
            )
            inserted += 1
        except Exception as e:
            print(f"Error inserting {f['name']}: {e}")
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": f"Seeded {inserted} foods."}), 200


# ────────────────────────────────────────────────────────────
# GET /api/meals/today
# ────────────────────────────────────────────────────────────
@meals_bp.route("/today", methods=["GET"])
@jwt_required()
def get_today():
    user_id = int(get_jwt_identity())
    today = date.today()
    return _get_plan_for_date(user_id, today)


# ────────────────────────────────────────────────────────────
# GET /api/meals/date/<date_str>
# ────────────────────────────────────────────────────────────
@meals_bp.route("/date/<date_str>", methods=["GET"])
@jwt_required()
def get_by_date(date_str):
    user_id = int(get_jwt_identity())
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    return _get_plan_for_date(user_id, d)


# ────────────────────────────────────────────────────────────
# POST /api/meals/swap
# ────────────────────────────────────────────────────────────
@meals_bp.route("/swap", methods=["POST"])
@jwt_required()
def swap_meal():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    meal_type = data.get("meal_type", "")
    date_str = data.get("date", str(date.today()))
    current_food = data.get("current_food", "")
    new_food = data.get("new_food", "")  # if provided, save this directly
    calorie_limit = data.get("calorie_limit", 9999)

    if not meal_type:
        return jsonify({"error": "meal_type is required."}), 400

    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        d = date.today()

    # Get user conditions & diet
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT diet, conditions FROM users WHERE id = %s",
        (user_id,),
    )
    user = cursor.fetchone()
    if not user:
        cursor.close()
        conn.close()
        return jsonify({"error": "User not found."}), 404

    user_diet = user.get("diet", "pureVegetarian")
    user_conditions = set(
        c.strip() for c in (user.get("conditions") or "").split(",") if c.strip()
    )

    if new_food:
        # Find exactly this food
        cursor.execute("SELECT * FROM foods WHERE name = %s LIMIT 1", (new_food,))
        exact_food = cursor.fetchone()
        cursor.close()
        if not exact_food:
            conn.close()
            return jsonify({"error": "Food not found."}), 404
        chosen = exact_food
    else:
        # Find candidates from foods table
        cursor.execute(
            "SELECT * FROM foods WHERE FIND_IN_SET(%s, meal_times) AND calories <= %s",
            (meal_type, calorie_limit),
        )
        all_foods = cursor.fetchall()
        cursor.close()

        # Filter by diet and conditions
        candidates = []
        for f in all_foods:
            # Diet filter
            if user_diet == "pureVegetarian" and f["diet"] not in ("pureVegetarian", "vegan"):
                continue
            if user_diet == "vegan" and f["diet"] != "vegan":
                continue
            # nonVegetarian can eat anything

            # Condition avoidance filter
            avoid = set(
                c.strip() for c in (f.get("avoid_for") or "").split(",") if c.strip()
            )
            if avoid & user_conditions:
                continue

            # Don't suggest same food
            if f["name"] == current_food:
                continue

            candidates.append(f)

        if not candidates:
            conn.close()
            return jsonify({"error": "No alternative foods found matching your filters."}), 404

        chosen_raw = random.choice(candidates)
        
        # Scale to a reasonable portion of the calorie_limit (e.g., 80% of limit)
        target_cals = int(calorie_limit * 0.8)
        raw_cals = chosen_raw.get("calories", 0)
        multiplier = (target_cals / raw_cals) if raw_cals > 0 else 1.0
        
        chosen = dict(chosen_raw)
        chosen["calories"] = int(raw_cals * multiplier)
        chosen["protein"] = int(chosen.get("protein", 0) * multiplier)
        chosen["carbs"] = int(chosen.get("carbs", 0) * multiplier)
        chosen["fat"] = int(chosen.get("fat", 0) * multiplier)
        chosen["subtitle"] = f"{chosen.get('subtitle', '')} (Scaled)"

        conn.close()
        return jsonify({
            "message": "Candidate found.",
            "meal": _food_to_dict(chosen, meal_type),
        }), 200

    # Update meal plan (only if new_food was provided)
    # Since new_food is passed by name, we need to fetch it and scale it again.
    # To keep it simple and accurate, we'll fetch it, then scale it similarly.
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM foods WHERE name = %s LIMIT 1", (new_food,))
    exact_food = cursor.fetchone()
    cursor.close()
    
    if exact_food:
        target_cals = int(calorie_limit * 0.8)
        raw_cals = exact_food.get("calories", 0)
        multiplier = (target_cals / raw_cals) if raw_cals > 0 else 1.0
        chosen = dict(exact_food)
        chosen["calories"] = int(raw_cals * multiplier)
        chosen["protein"] = int(chosen.get("protein", 0) * multiplier)
        chosen["carbs"] = int(chosen.get("carbs", 0) * multiplier)
        chosen["fat"] = int(chosen.get("fat", 0) * multiplier)
        chosen["subtitle"] = f"{chosen.get('subtitle', '')} (Scaled)"
    else:
        # Fallback if somehow not found
        chosen = {"name": new_food, "emoji": "", "calories": 0, "protein": 0, "carbs": 0, "fat": 0, "subtitle": "", "ingredients": ""}

    cur2 = conn.cursor()
    cur2.execute(
        """INSERT INTO meal_plans
           (user_id, plan_date, meal_type, food_name, emoji, calories, protein, carbs, fat, subtitle, ingredients)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE
               food_name = VALUES(food_name),
               emoji = VALUES(emoji),
               calories = VALUES(calories),
               protein = VALUES(protein),
               carbs = VALUES(carbs),
               fat = VALUES(fat),
               subtitle = VALUES(subtitle),
               ingredients = VALUES(ingredients)""",
        (
            user_id, d, meal_type,
            chosen["name"], chosen.get("emoji", ""), chosen.get("calories", 0),
            chosen.get("protein", 0), chosen.get("carbs", 0), chosen.get("fat", 0),
            chosen.get("subtitle", ""), chosen.get("ingredients", ""),
        ),
    )
    conn.commit()
    cur2.close()
    conn.close()

    return jsonify({
        "message": "Meal swapped.",
        "meal": _food_to_dict(chosen, meal_type),
    }), 200


# ────────────────────────────────────────────────────────────
# GET /api/foods  — full food database
# ────────────────────────────────────────────────────────────
@meals_bp.route("/foods", methods=["GET"])
@jwt_required()
def get_foods():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM foods ORDER BY name")
    foods = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify({
        "foods": [_raw_food_dict(f) for f in foods]
    }), 200


# ────────────────────────────────────────────────────────────
# GET /api/foods/safe  — foods safe for user's conditions
# ────────────────────────────────────────────────────────────
@meals_bp.route("/foods/safe", methods=["GET"])
@jwt_required()
def get_safe_foods():
    user_id = int(get_jwt_identity())

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT conditions, diet FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        return jsonify({"error": "User not found."}), 404

    user_conditions = set(
        c.strip() for c in (user.get("conditions") or "").split(",") if c.strip()
    )
    user_diet = user.get("diet", "pureVegetarian")

    cursor.execute("SELECT * FROM foods ORDER BY name")
    all_foods = cursor.fetchall()
    cursor.close()
    conn.close()

    safe = []
    for f in all_foods:
        if user_diet == "pureVegetarian" and f["diet"] not in ("pureVegetarian", "vegan"):
            continue
        if user_diet == "vegan" and f["diet"] != "vegan":
            continue
        avoid = set(c.strip() for c in (f.get("avoid_for") or "").split(",") if c.strip())
        if avoid & user_conditions:
            continue
        safe.append(_raw_food_dict(f))

    return jsonify({"foods": safe}), 200


# ────────────────────────────────────────────────────────────
# Internal helpers
# ────────────────────────────────────────────────────────────
def _get_plan_for_date(user_id, d):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM meal_plans WHERE user_id = %s AND plan_date = %s",
        (user_id, d),
    )
    plans = cursor.fetchall()

    if not plans:
        # Auto-generate plan
        _generate_plan(user_id, d, conn)
        cursor.execute(
            "SELECT * FROM meal_plans WHERE user_id = %s AND plan_date = %s",
            (user_id, d),
        )
        plans = cursor.fetchall()

    cursor.close()
    conn.close()

    meals = {}
    total_cal = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0
    for p in plans:
        meals[p["meal_type"]] = {
            "food_name": p["food_name"],
            "emoji": p["emoji"],
            "calories": p["calories"],
            "protein": p["protein"],
            "carbs": p["carbs"],
            "fat": p["fat"],
            "subtitle": p["subtitle"],
            "ingredients": p.get("ingredients", ""),
        }
        total_cal += p["calories"]
        total_protein += p["protein"]
        total_carbs += p["carbs"]
        total_fat += p["fat"]

    return jsonify({
        "date": str(d),
        "meals": meals,
        "totals": {
            "calories": total_cal,
            "protein": total_protein,
            "carbs": total_carbs,
            "fat": total_fat,
        },
    }), 200


def _generate_plan(user_id, d, conn):
    """Auto-generate a day's meal plan based on user conditions and diet."""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT age, gender, weight_kg, height_cm, diet, conditions FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        return

    # Calculate user's required goal (BMR * 1.375)
    age = user.get("age") or 28
    weight = user.get("weight_kg") or 74.5
    height = user.get("height_cm") or 178
    gender = user.get("gender") or "Male"
    
    if gender.lower() == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    elif gender.lower() == "female":
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 80
        
    daily_goal = round(bmr * 1.375)

    user_diet = user.get("diet", "pureVegetarian")
    user_conditions = set(
        c.strip() for c in (user.get("conditions") or "").split(",") if c.strip()
    )

    cursor.execute("SELECT * FROM foods")
    all_foods = cursor.fetchall()
    cursor.close()

    # Group by meal type
    by_meal_type = {"Breakfast": [], "Lunch": [], "Dinner": [], "Snack": []}
    for f in all_foods:
        # Diet filter
        if user_diet == "pureVegetarian" and f["diet"] not in ("pureVegetarian", "vegan"):
            continue
        if user_diet == "vegan" and f["diet"] != "vegan":
            continue

        # Condition avoidance filter
        avoid = set(c.strip() for c in (f.get("avoid_for") or "").split(",") if c.strip())
        if avoid & user_conditions:
            continue

        meal_times = [mt.strip() for mt in (f.get("meal_times") or "").split(",")]
        for mt in meal_times:
            if mt in by_meal_type:
                by_meal_type[mt].append(f)

    # Pick random meals and calculate raw total
    selected_meals = {}
    raw_total = 0
    for meal_type in ["Breakfast", "Lunch", "Dinner", "Snack"]:
        candidates = by_meal_type.get(meal_type, [])
        if candidates:
            chosen = random.choice(candidates)
            selected_meals[meal_type] = chosen
            raw_total += chosen.get("calories", 0)

    # Scale to match the user's daily goal
    multiplier = (daily_goal / raw_total) if raw_total > 0 else 1.0

    cursor2 = conn.cursor()
    for meal_type, chosen_raw in selected_meals.items():
        scaled_cals = int(chosen_raw.get("calories", 0) * multiplier)
        scaled_p = int(chosen_raw.get("protein", 0) * multiplier)
        scaled_c = int(chosen_raw.get("carbs", 0) * multiplier)
        scaled_f = int(chosen_raw.get("fat", 0) * multiplier)
        subtitle = f"{chosen_raw.get('subtitle', '')} (Scaled)"

        try:
            cursor2.execute(
                """INSERT INTO meal_plans
                   (user_id, plan_date, meal_type, food_name, emoji, calories, protein, carbs, fat, subtitle, ingredients)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE
                       food_name = VALUES(food_name),
                       emoji = VALUES(emoji),
                       calories = VALUES(calories),
                       protein = VALUES(protein),
                       carbs = VALUES(carbs),
                       fat = VALUES(fat),
                       subtitle = VALUES(subtitle),
                       ingredients = VALUES(ingredients)""",
                (
                    user_id, d, meal_type,
                    chosen_raw["name"], chosen_raw.get("emoji", ""), scaled_cals,
                    scaled_p, scaled_c, scaled_f,
                    subtitle, chosen_raw.get("ingredients", ""),
                ),
            )
        except Exception:
            pass
    conn.commit()
    cursor2.close()


def _food_to_dict(f, meal_type):
    return {
        "meal_type": meal_type,
        "food_name": f["name"],
        "emoji": f.get("emoji", ""),
        "calories": f.get("calories", 0),
        "protein": f.get("protein", 0),
        "carbs": f.get("carbs", 0),
        "fat": f.get("fat", 0),
        "subtitle": f.get("subtitle", ""),
        "ingredients": f.get("ingredients", ""),
    }


def _raw_food_dict(f):
    return {
        "id": f["id"],
        "name": f["name"],
        "emoji": f.get("emoji", ""),
        "calories": f.get("calories", 0),
        "protein": f.get("protein", 0),
        "carbs": f.get("carbs", 0),
        "fat": f.get("fat", 0),
        "diet": f.get("diet", ""),
        "avoid_for": f.get("avoid_for", ""),
        "safe_for": f.get("safe_for", ""),
        "meal_times": f.get("meal_times", ""),
        "subtitle": f.get("subtitle", ""),
        "ingredients": f.get("ingredients", ""),
    }
