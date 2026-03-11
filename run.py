from app import create_app
import threading
from app.worker import worker_loop   # make sure this function exists

app = create_app()


def start_worker():
    thread = threading.Thread(target=worker_loop)
    thread.daemon = True
    thread.start()


# start worker when app starts
start_worker()