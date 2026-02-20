import subprocess
import tempfile
import os
from ..models import Submission, TestCase
import time,psutil

def run_python_code_docker(code:str,input_data:str,time_limit:int, memory_limit:int):
    file_path=judge_submission(code)
    file_name=os.path.basename(file_path)
    dir_path=os.path.dirname(os.path.abspath(file_path))

    memory_limit_str=f"{memory_limit}m"
    start=time.time()

    try:
        cmd = [
            "docker", "run",
            "--rm",
            "-i",
            "--memory", memory_limit_str,
            "--cpus", "1",
            "--network", "none",
            "-v", f"{dir_path}:/app",
            "-w", "/app",
            "python:3.11-slim",
            "python", file_name
        ]

        print("DOCKER CMD:", cmd)

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout_data, stderr_data = process.communicate(
            input=input_data,
            timeout=(time_limit / 1000 )+5 # convert ms to seconds
        )

        end = time.time()
        execution_time = (end - start) * 1000

        return {
            "stdout": stdout_data,
            "stderr": stderr_data,
            "timeout": False,
            "memory_exceeded": False,
            "returncode": process.returncode,
            "time_taken": execution_time,
            "memory_taken": None  # Docker handles memory limit
        }

    except subprocess.TimeoutExpired:
        process.kill()
        return {
            "stdout": "",
            "stderr": "Time Limit Exceeded",
            "timeout": True,
            "memory_exceeded": False,
            "returncode": None,
            "time_taken": time_limit,
            "memory_taken": None
        }

    finally:
        os.remove(file_path)
import uuid

def judge_submission(code: str):
    base_dir = os.path.abspath("tmp")
    os.makedirs(base_dir, exist_ok=True)

    file_name = f"{uuid.uuid4().hex}.py"
    file_path = os.path.join(base_dir, file_name)

    with open(file_path, "w") as f:
        f.write(code)

    return file_path

def run_python_code(code:str,input_data:str,time_limit:int, memory_limit:int):
    file_path=judge_submission(code)
    try:
        start=time.time()
        memory_limit_bytes=memory_limit*1024*1024
        memory_exceeded=False

        process=subprocess.Popen(
            ['python', file_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        proc=psutil.Process(process.pid)
        max_memory=0

        process.stdin.write(input_data)
        process.stdin.close()

        while process.poll() is None:
            elapsed_time=(time.time()-start)*1000
            timeout=False
            memory_exceeded=False
            if elapsed_time>time_limit:
                process.kill()
                timeout=True
                break

            try:
                mem_info=proc.memory_info()
                current_memory=mem_info.rss
                max_memory=max(max_memory, current_memory)

                if current_memory>memory_limit_bytes:
                    memory_exceeded=True
                    process.kill()
                    break

            except psutil.NoSuchProcess:
                break  
            time.sleep(0.01)

        stdout_data, stderr_data = process.communicate()
        end=time.time()
        execution_time=(end-start)*1000

        return{
            "stdout": stdout_data if not memory_exceeded else "",
            "stderr": "Memory Limit Exceeded" if memory_exceeded else stderr_data,
            "timeout": False,
            "returncode": None if memory_exceeded else process.returncode,
            "time_taken": execution_time,
            "memory_taken": max_memory
        }
    
    finally:
        os.remove(file_path)
    
    
def judge_against_testcases(submission,test_cases):
    max_time=0
    max_memory=0
    if not test_cases:
        return {"verdict": "No Test Cases","time_taken": 0,"memory_taken": 0}
    for test_case in test_cases:
        result=run_python_code(
            submission.code,
            test_case.input_data,
            submission.problem.time_limit
        )
        max_time=max(max_time,result["time_taken"])
        max_memory=max(max_memory,result["memory_taken"])
        if result["timeout"]:
            return {"verdict": "Time Limit Exceeded", "time_taken": max_time, "memory_taken": max_memory}
        if result["returncode"]!=0:
            return {"verdict": "Runtime Error", "time_taken": max_time, "memory_taken": max_memory}
        if result["stdout"].strip() != test_case.expected_output.strip():
            return {"verdict": "Wrong Answer", "time_taken": max_time, "memory_taken": max_memory}
        
        
    return {"verdict": "Accepted", "time_taken": max_time, "memory_taken": max_memory}

