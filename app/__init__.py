from flask import Flask
from .extentions import db, jwt
from .routes import register_routes
from flask_migrate import Migrate
from datetime import timedelta
import os


def create_app():

    app = Flask(__name__, template_folder="templates")

    app.config["JWT_SECRET_KEY"] = "dev-secret-key"
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db_url = os.getenv("DATABASE_URL")

    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///local.db"

    db.init_app(app)
    migrate = Migrate(app, db)
    jwt.init_app(app)

    # 🔴 THIS IS IMPORTANT
    from . import models

    register_routes(app)

    return app