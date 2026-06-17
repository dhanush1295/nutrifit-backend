"""
Database seeder – creates tables and inserts all food items from the NutriFit food database.
Run:  python3 seed_db.py
"""

import mysql.connector
from config import Config
from db import create_tables, get_db


def create_database():
    """Ensure the database exists (connects without specifying a database)."""
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Database '{Config.MYSQL_DATABASE}' ready.")


# ────────────────────────────────────────────────────────────
# Food data (mirrored from FoodDatabase.swift)
# ────────────────────────────────────────────────────────────
FOODS = [
    # ── BREAKFAST ──
    {
        "name": "Vegetable Poha", "emoji": "🥣", "calories": 220,
        "protein": 6, "carbs": 38, "fat": 5,
        "diet": "pureVegetarian",
        "avoid_for": "", "safe_for": "diabetes,cholesterol",
        "meal_times": "Breakfast",
        "subtitle": "Low GI • High Fiber",
        "ingredients": "Flattened rice, vegetables, peanuts, turmeric, curry leaves"
    },
    {
        "name": "Idli with Sambar", "emoji": "🍛", "calories": 250,
        "protein": 8, "carbs": 46, "fat": 3,
        "diet": "pureVegetarian",
        "avoid_for": "diabetes", "safe_for": "ibs,cholesterol",
        "meal_times": "Breakfast",
        "subtitle": "Light Fermented Food • Probiotic",
        "ingredients": "Steamed rice-lentil cakes, lentil vegetable stew, coconut chutney"
    },
    {
        "name": "Moong Dal Chilla", "emoji": "🫓", "calories": 200,
        "protein": 12, "carbs": 28, "fat": 4,
        "diet": "vegan",
        "avoid_for": "", "safe_for": "diabetes,pcos,cholesterol",
        "meal_times": "Breakfast",
        "subtitle": "High Protein • Gluten Free",
        "ingredients": "Yellow lentil batter, green chillies, ginger, coriander"
    },
    {
        "name": "Oats Upma", "emoji": "🥣", "calories": 230,
        "protein": 7, "carbs": 36, "fat": 6,
        "diet": "vegan",
        "avoid_for": "", "safe_for": "diabetes,cholesterol,hypertension",
        "meal_times": "Breakfast",
        "subtitle": "Anti-inflammatory • Low GI",
        "ingredients": "Rolled oats, mustard seeds, curry leaves, vegetables, coconut oil"
    },
    {
        "name": "Besan Chilla", "emoji": "🫓", "calories": 210,
        "protein": 10, "carbs": 24, "fat": 7,
        "diet": "vegan",
        "avoid_for": "", "safe_for": "diabetes,pcos",
        "meal_times": "Breakfast",
        "subtitle": "Protein Rich • Low Carb",
        "ingredients": "Chickpea flour, onion, tomato, green chilli, coriander"
    },
    {
        "name": "Ragi Dosa with Chutney", "emoji": "🥞", "calories": 240,
        "protein": 7, "carbs": 42, "fat": 5,
        "diet": "vegan",
        "avoid_for": "", "safe_for": "diabetes,cholesterol,hypertension",
        "meal_times": "Breakfast",
        "subtitle": "Calcium Rich • Low GI",
        "ingredients": "Finger millet batter, coconut chutney, sambar"
    },
    {
        "name": "Egg White Omelette (Anda Bhurji Style)", "emoji": "🍳", "calories": 190,
        "protein": 18, "carbs": 6, "fat": 5,
        "diet": "nonVegetarian",
        "avoid_for": "", "safe_for": "cholesterol,diabetes,pcos",
        "meal_times": "Breakfast",
        "subtitle": "High Protein • Low Fat",
        "ingredients": "Egg whites, onion, tomato, green chilli, coriander, turmeric"
    },
    {
        "name": "Paneer Paratha (Thin)", "emoji": "🫓", "calories": 320,
        "protein": 14, "carbs": 38, "fat": 12,
        "diet": "pureVegetarian",
        "avoid_for": "cholesterol,ckd", "safe_for": "pcos",
        "meal_times": "Breakfast",
        "subtitle": "High Protein • Filling",
        "ingredients": "Whole wheat flour, paneer stuffing, minimal ghee, curd"
    },
    {
        "name": "Curd (Dahi) with Pomegranate", "emoji": "🍶", "calories": 180,
        "protein": 8, "carbs": 28, "fat": 2,
        "diet": "pureVegetarian",
        "avoid_for": "", "safe_for": "diabetes,hypertension,ibs",
        "meal_times": "Breakfast,Snack",
        "subtitle": "Probiotic • Antioxidant",
        "ingredients": "Low-fat curd, pomegranate seeds, a drizzle of honey"
    },
    {
        "name": "Chia Pudding with Mango", "emoji": "🍮", "calories": 195,
        "protein": 6, "carbs": 28, "fat": 8,
        "diet": "vegan",
        "avoid_for": "", "safe_for": "diabetes,pcos,hypertension",
        "meal_times": "Breakfast,Snack",
        "subtitle": "Omega-3 Rich • Low GI",
        "ingredients": "Chia seeds, almond milk, fresh mango pulp"
    },
    {
        "name": "Poha with Sprouts", "emoji": "🥗", "calories": 240,
        "protein": 10, "carbs": 40, "fat": 5,
        "diet": "vegan",
        "avoid_for": "", "safe_for": "diabetes,cholesterol",
        "meal_times": "Breakfast",
        "subtitle": "High Fiber • Protein Boost",
        "ingredients": "Flattened rice, moong sprouts, peanuts, mustard, lemon"
    },

    # ── LUNCH ──
    {
        "name": "Dal Tadka with Brown Rice", "emoji": "🍲", "calories": 410,
        "protein": 18, "carbs": 65, "fat": 8,
        "diet": "pureVegetarian",
        "avoid_for": "", "safe_for": "diabetes,cholesterol,hypertension",
        "meal_times": "Lunch,Dinner",
        "subtitle": "Plant Protein • High Fiber",
        "ingredients": "Yellow lentils, brown rice, cumin, garlic, ghee tadka"
    },
    {
        "name": "Rajma Chawal", "emoji": "🫘", "calories": 430,
        "protein": 17, "carbs": 72, "fat": 7,
        "diet": "vegan",
        "avoid_for": "ibs,ckd", "safe_for": "diabetes,cholesterol",
        "meal_times": "Lunch,Dinner",
        "subtitle": "High Protein • Iron Rich",
        "ingredients": "Kidney beans, basmati rice, tomato-onion gravy, spices"
    },
    {
        "name": "Palak Paneer with Roti", "emoji": "🧀", "calories": 450,
        "protein": 20, "carbs": 44, "fat": 18,
        "diet": "pureVegetarian",
        "avoid_for": "cholesterol,ckd", "safe_for": "diabetes,thyroid,pcos",
        "meal_times": "Lunch,Dinner",
        "subtitle": "Iron Rich • Calcium Boost",
        "ingredients": "Spinach puree, paneer, whole wheat roti, mild spices"
    },
    {
        "name": "Tofu & Vegetable Curry with Quinoa", "emoji": "🥘", "calories": 380,
        "protein": 20, "carbs": 42, "fat": 12,
        "diet": "vegan",
        "avoid_for": "", "safe_for": "diabetes,pcos,cholesterol,hypertension",
        "meal_times": "Lunch,Dinner",
        "subtitle": "High Protein • Low GI",
        "ingredients": "Firm tofu, mixed vegetables, quinoa, coconut milk curry"
    },
    {
        "name": "Chicken Rogan Josh", "emoji": "🍗", "calories": 420,
        "protein": 38, "carbs": 28, "fat": 14,
        "diet": "nonVegetarian",
        "avoid_for": "ckd", "safe_for": "diabetes,pcos",
        "meal_times": "Lunch,Dinner",
        "subtitle": "Lean Protein • High Iron",
        "ingredients": "Chicken, Kashmiri chillies, yoghurt, whole spices, steamed rice"
    },
    {
        "name": "Fish Curry with Brown Rice", "emoji": "🐟", "calories": 400,
        "protein": 35, "carbs": 36, "fat": 12,
        "diet": "nonVegetarian",
        "avoid_for": "ckd", "safe_for": "pcos,cholesterol,hypertension,thyroid",
        "meal_times": "Lunch,Dinner",
        "subtitle": "Omega-3 • Anti-inflammatory",
        "ingredients": "Rohu/Pomfret fish, coconut-mustard curry, brown rice"
    },
    {
        "name": "Mixed Dal with Jowar Roti", "emoji": "🍲", "calories": 360,
        "protein": 16, "carbs": 58, "fat": 5,
        "diet": "vegan",
        "avoid_for": "", "safe_for": "diabetes,cholesterol,hypertension,ibs",
        "meal_times": "Lunch,Dinner",
        "subtitle": "Gluten Free • Low GI",
        "ingredients": "Mixed lentils, sorghum flatbread, ginger-garlic tadka"
    },
    {
        "name": "Chole with Bhatura (Baked)", "emoji": "🥙", "calories": 480,
        "protein": 16, "carbs": 74, "fat": 14,
        "diet": "vegan",
        "avoid_for": "ibs,ckd", "safe_for": "",
        "meal_times": "Lunch",
        "subtitle": "High Protein • Filling",
        "ingredients": "Chickpeas, baked bhatura, onion-tomato masala"
    },
    {
        "name": "Vegetable Biryani (Low Oil)", "emoji": "🍛", "calories": 390,
        "protein": 10, "carbs": 68, "fat": 8,
        "diet": "pureVegetarian",
        "avoid_for": "", "safe_for": "hypertension,cholesterol",
        "meal_times": "Lunch,Dinner",
        "subtitle": "Aromatic • Balanced Meal",
        "ingredients": "Basmati rice, seasonal vegetables, saffron, whole spices, raita"
    },
    {
        "name": "Prawn Masala with Steamed Rice", "emoji": "🦐", "calories": 370,
        "protein": 30, "carbs": 34, "fat": 9,
        "diet": "nonVegetarian",
        "avoid_for": "cholesterol,ckd", "safe_for": "pcos,thyroid",
        "meal_times": "Lunch,Dinner",
        "subtitle": "Low Fat • High Protein",
        "ingredients": "Tiger prawns, coconut-tomato masala, steamed rice"
    },
    {
        "name": "Sambar with Idli & Vegetables", "emoji": "🍲", "calories": 340,
        "protein": 12, "carbs": 56, "fat": 4,
        "diet": "vegan",
        "avoid_for": "", "safe_for": "ibs,cholesterol,hypertension",
        "meal_times": "Lunch,Dinner",
        "subtitle": "Light & Digestive",
        "ingredients": "Tamarind-lentil broth, vegetables, idli, coconut chutney"
    },
    {
        "name": "Paneer Tikka with Salad", "emoji": "🍢", "calories": 350,
        "protein": 22, "carbs": 16, "fat": 20,
        "diet": "pureVegetarian",
        "avoid_for": "cholesterol,ckd", "safe_for": "pcos,diabetes",
        "meal_times": "Lunch,Dinner",
        "subtitle": "High Protein • Low Carb",
        "ingredients": "Paneer, bell peppers, yoghurt marinade, green salad"
    },
    {
        "name": "Egg Curry with Multigrain Roti", "emoji": "🍛", "calories": 410,
        "protein": 26, "carbs": 40, "fat": 14,
        "diet": "nonVegetarian",
        "avoid_for": "", "safe_for": "pcos,diabetes,thyroid",
        "meal_times": "Lunch,Dinner",
        "subtitle": "Protein Packed • Balanced",
        "ingredients": "Hard-boiled eggs, onion-tomato gravy, multigrain roti"
    },

    # ── DINNER ──
    {
        "name": "Moong Dal Khichdi", "emoji": "🥣", "calories": 320,
        "protein": 14, "carbs": 54, "fat": 6,
        "diet": "pureVegetarian",
        "avoid_for": "", "safe_for": "diabetes,ibs,ckd,cholesterol,hypertension",
        "meal_times": "Dinner",
        "subtitle": "Easy to Digest • Healing",
        "ingredients": "Moong dal, rice, turmeric, ginger, ghee, vegetables"
    },
    {
        "name": "Palak Dal with Bajra Roti", "emoji": "🥬", "calories": 360,
        "protein": 16, "carbs": 52, "fat": 7,
        "diet": "vegan",
        "avoid_for": "", "safe_for": "diabetes,hypertension,cholesterol,thyroid",
        "meal_times": "Dinner",
        "subtitle": "Iron & Fiber Rich",
        "ingredients": "Spinach, lentils, pearl millet roti, garlic tadka"
    },
    {
        "name": "Grilled Chicken Breast & Stir-Fry", "emoji": "🍗", "calories": 350,
        "protein": 40, "carbs": 14, "fat": 10,
        "diet": "nonVegetarian",
        "avoid_for": "ckd", "safe_for": "diabetes,pcos,cholesterol",
        "meal_times": "Dinner",
        "subtitle": "Lean Protein • Low Carb",
        "ingredients": "Chicken breast, stir-fried vegetables, minimal oil, spices"
    },
    {
        "name": "Vegetable Soup with Whole Wheat Bread", "emoji": "🍵", "calories": 240,
        "protein": 8, "carbs": 40, "fat": 4,
        "diet": "vegan",
        "avoid_for": "", "safe_for": "hypertension,cholesterol,ibs,ckd",
        "meal_times": "Dinner",
        "subtitle": "Light • Low Calorie",
        "ingredients": "Seasonal vegetables, whole wheat bread, herbs, low-sodium broth"
    },
    {
        "name": "Toor Dal with Bajra Bhakri", "emoji": "🍲", "calories": 340,
        "protein": 14, "carbs": 56, "fat": 5,
        "diet": "vegan",
        "avoid_for": "ibs", "safe_for": "diabetes,hypertension,cholesterol",
        "meal_times": "Dinner",
        "subtitle": "Fiber Rich • Satisfying",
        "ingredients": "Toor dal, bajra bhakri, kokum, jaggery, garlic"
    },

    # ── SNACKS ──
    {
        "name": "Roasted Chana", "emoji": "🍿", "calories": 150,
        "protein": 8, "carbs": 22, "fat": 3,
        "diet": "vegan",
        "avoid_for": "ibs", "safe_for": "diabetes,cholesterol,pcos",
        "meal_times": "Snack",
        "subtitle": "Low GI • High Protein",
        "ingredients": "Dry-roasted chickpeas, spices"
    },
    {
        "name": "Mixed Nuts & Seeds", "emoji": "🌰", "calories": 160,
        "protein": 5, "carbs": 8, "fat": 13,
        "diet": "vegan",
        "avoid_for": "ibs,ckd", "safe_for": "cholesterol,pcos,hypertension,thyroid",
        "meal_times": "Snack",
        "subtitle": "Healthy Fats • Brain Food",
        "ingredients": "Almonds, walnuts, pumpkin seeds, sunflower seeds"
    },
    {
        "name": "Sprout Chaat", "emoji": "🥗", "calories": 130,
        "protein": 8, "carbs": 20, "fat": 1,
        "diet": "vegan",
        "avoid_for": "", "safe_for": "diabetes,pcos,cholesterol,hypertension",
        "meal_times": "Snack",
        "subtitle": "Raw Protein • Vitamin C",
        "ingredients": "Mixed sprouts, tomato, onion, lemon, chaat masala"
    },
    {
        "name": "Boiled Egg (Masala)", "emoji": "🥚", "calories": 90,
        "protein": 7, "carbs": 1, "fat": 6,
        "diet": "nonVegetarian",
        "avoid_for": "", "safe_for": "pcos,diabetes,thyroid",
        "meal_times": "Snack",
        "subtitle": "High Quality Protein",
        "ingredients": "Hard-boiled egg, chaat masala, lemon"
    },
    {
        "name": "Cucumber & Mint Raita", "emoji": "🥒", "calories": 90,
        "protein": 5, "carbs": 10, "fat": 1,
        "diet": "pureVegetarian",
        "avoid_for": "", "safe_for": "hypertension,cholesterol,ibs,diabetes",
        "meal_times": "Snack",
        "subtitle": "Low Calorie • Cooling",
        "ingredients": "Low-fat curd, cucumber, mint, cumin powder"
    },
    {
        "name": "Makhana (Foxnuts) Roasted", "emoji": "🫙", "calories": 120,
        "protein": 4, "carbs": 22, "fat": 3,
        "diet": "vegan",
        "avoid_for": "", "safe_for": "diabetes,hypertension,cholesterol,ckd",
        "meal_times": "Snack",
        "subtitle": "Low Sodium • Antioxidant",
        "ingredients": "Foxnuts, ghee, sendha namak, spices"
    },
    {
        "name": "Dhokla", "emoji": "🍰", "calories": 140,
        "protein": 6, "carbs": 24, "fat": 2,
        "diet": "vegan",
        "avoid_for": "", "safe_for": "diabetes,cholesterol,hypertension,ibs",
        "meal_times": "Snack,Breakfast",
        "subtitle": "Fermented • Low Fat",
        "ingredients": "Chickpea flour, yoghurt, eno, green chilli, mustard seeds"
    },
    {
        "name": "Masala Chaas (Buttermilk)", "emoji": "🥛", "calories": 60,
        "protein": 3, "carbs": 6, "fat": 1,
        "diet": "pureVegetarian",
        "avoid_for": "", "safe_for": "diabetes,hypertension,ibs,cholesterol",
        "meal_times": "Snack",
        "subtitle": "Probiotic • Digestive",
        "ingredients": "Low-fat buttermilk, cumin, mint, black salt"
    },
]


def seed_foods():
    """Insert all food items into the foods table (skip duplicates)."""
    conn = get_db()
    cursor = conn.cursor()

    # Clear existing
    cursor.execute("DELETE FROM foods")

    for f in FOODS:
        cursor.execute(
            """INSERT INTO foods
               (name, emoji, calories, protein, carbs, fat, diet, avoid_for, safe_for, meal_times, subtitle, ingredients)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                f["name"], f["emoji"], f["calories"],
                f["protein"], f["carbs"], f["fat"],
                f["diet"], f["avoid_for"], f["safe_for"],
                f["meal_times"], f["subtitle"], f["ingredients"],
            ),
        )

    conn.commit()
    print(f"✅ Seeded {len(FOODS)} food items.")
    cursor.close()
    conn.close()


if __name__ == "__main__":
    print("🔧 NutriFit Database Setup")
    print("-" * 40)

    # 1. Create database
    create_database()

    # 2. Create tables
    create_tables()
    print("✅ All tables created.")

    # 3. Seed food database
    seed_foods()

    print("-" * 40)
    print("🎉 Database setup complete!")
