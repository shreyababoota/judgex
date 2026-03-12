from app import create_app
from app.extentions import db
from app.judge.worker import run_worker
from flask_migrate import upgrade
import threading

app = create_app()

# apply migrations automatically
with app.app_context():
    upgrade()


def start_worker():
    def worker():
        print("Judge worker started")
        run_worker(app)

    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()


start_worker()


if __name__ == "__main__":
    app.run(debug=True)