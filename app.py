"""
ReqCraft AI - Application Entry Point
AI-Based SRS Generator and Quality Checker (FYP-1)

Run:  python app.py
"""
import os
import logging

from flask import Flask
from flask_login import LoginManager

from config import Config
from models.database import db, User

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access ReqCraft AI."
login_manager.login_message_category = "warning"


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure required folders exist
    for folder in ("instance", Config.UPLOAD_FOLDER, Config.EXPORT_FOLDER):
        os.makedirs(folder, exist_ok=True)

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Create tables
    with app.app_context():
        db.create_all()

    return app


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
