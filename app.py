"""
NutriFit Flask Backend — main application entry-point.
Run with: python3 app.py
"""

import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

from config import Config

# Blueprints
from routes.auth import auth_bp
from routes.profile import profile_bp
from routes.meals import meals_bp
from routes.intake import intake_bp
from routes.coach import coach_bp
from routes.notifications import notifications_bp


def create_app():
    app = Flask(__name__)

    # Config
    app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = Config.JWT_ACCESS_TOKEN_EXPIRES

    # Extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    Bcrypt(app)
    JWTManager(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(meals_bp)
    app.register_blueprint(intake_bp)
    app.register_blueprint(coach_bp)
    app.register_blueprint(notifications_bp)

    # Health check
    @app.route("/api/health", methods=["GET"])
    def health():
        return {"status": "ok", "service": "NutriFit API"}, 200

    # Serve uploads
    @app.route("/uploads/<filename>")
    def uploaded_file(filename):
        uploads_dir = os.path.join(app.root_path, "uploads")
        return send_from_directory(uploads_dir, filename)

    return app


if __name__ == "__main__":
    app = create_app()
    print("=" * 50)
    print("  NutriFit API Server")
    print("  http://localhost:5001")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5001, debug=True)
