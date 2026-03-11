from app import create_app
from app.extentions import db
import threading
from app.judge.worker import run_worker

app = create_app()

with app.app_context():
    db.create_all()

def start_worker():
    thread = threading.Thread(target=run_worker)
    thread.daemon = True
    thread.start()

if __name__ == "__main__":
    start_worker()
    app.run(debug=True)