from flask import Flask
from .extentions import db, jwt
from .routes import register_routes
from flask_migrate import Migrate
from app.routes.admin import admin_bp
from datetime import timedelta
import os

def create_app():
    app = Flask(__name__, template_folder="templates")

    app.config["JWT_SECRET_KEY"] ="dev-secret-key"

    database_url = os.environ.get("DATABASE_URL")

    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)

    app.register_blueprint(admin_bp)

    db.init_app(app)
    migrate = Migrate(app, db)
    jwt.init_app(app)

    register_routes(app)

    return app