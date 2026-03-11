from app import create_app
import threading
from app.judge.worker import run_worker

app = create_app()


def start_worker():
    thread = threading.Thread(target=run_worker)
    thread.daemon = True
    thread.start()


start_worker()