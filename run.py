from app import create_app
from app.extentions import db
from app.judge.worker import run_worker
import threading

app = create_app()

# create tables if they don't exist
with app.app_context():
    db.create_all()


def start_worker():
    def worker():
        with app.app_context():
            print("Judge worker started")
            run_worker()

    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()

start_worker()


if __name__ == "__main__":
    app.run(debug=True)