from flask import Flask
from .extentions import db, jwt
from .routes import register_routes
from flask_migrate import Migrate
from app.routes.admin import admin_bp
from datetime import timedelta

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config["JWT_SECRET_KEY"] ="dev-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:Shreya%4028904@localhost:5432/auth_db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
    app.register_blueprint(admin_bp)

    db.init_app(app)
    migrate=Migrate(app,db)
    jwt.init_app(app)
    
    register_routes(app)

    return app