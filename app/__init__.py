from flask import Flask
from .extentions import db, jwt
from .routes import register_routes
from flask_migrate import Migrate
from datetime import timedelta
import os
import threading
import atexit


def create_app():

    app = Flask(__name__, template_folder="templates", instance_relative_config=True)

    # Ensure folders exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "submissions_storage"), exist_ok=True)

    # Config
    app.config["JWT_SECRET_KEY"] = "dev-secret-key"
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db_url = os.getenv("DATABASE_URL")

    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)

        app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(app.instance_path, "local.db")

    # Init extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt.init_app(app)

    from . import models
    register_routes(app)

    # -------- START WORKER THREAD --------

    stop_event = threading.Event()

    def start_worker():
        from app.judge.worker import run_worker
        run_worker(app, stop_event)

    # Prevent multiple workers when Flask reloads
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        worker_thread = threading.Thread(target=start_worker, daemon=True)
        worker_thread.start()

    # Clean shutdown
    @atexit.register
    def shutdown_worker():
        stop_event.set()

    return app