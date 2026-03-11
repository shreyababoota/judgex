from multiprocessing import Process
from app.judge.worker import run_worker
import os

def start_worker():
    run_worker()

def main():
    workers=[]

    for _ in range(os.cpu_count()):
        p=Process(target=start_worker)
        p.start()
        workers.append(p)

    for p in workers:
        p.join()
    
if __name__=="__main__":
    main()