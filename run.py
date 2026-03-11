from app import create_app
from app.extentions import db

app = create_app()

def ensure_tables():
    with app.app_context():
        db.create_all()
        print("Tables ensured")

ensure_tables()