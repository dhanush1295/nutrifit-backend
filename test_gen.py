from datetime import date
from db import get_db
from routes.meals import _get_plan_for_date

def test():
    # User 4 is Kiran (hypertension,diabetes, nonVegetarian)
    res, status = _get_plan_for_date(4, date.today())
    print(status)
    print(res.get_json())

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        test()
