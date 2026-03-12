import subprocess
import os
import time
import resource


def limit_memory(memory_mb):
    memory_bytes = memory_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))


def run_code(command, input_data, time_limit, memory_limit, work_dir):

    start_time = time.perf_counter()

    usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)

    try:
        result = subprocess.run(
            command,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=time_limit / 1000,
            cwd=work_dir,
            preexec_fn=lambda: limit_memory(memory_limit),
        )

        end_time = time.perf_counter()

        usage_after = resource.getrusage(resource.RUSAGE_CHILDREN)

        memory_used = usage_after.ru_maxrss - usage_before.ru_maxrss

        stdout_data = result.stdout
        stderr_data = result.stderr

        if len(stdout_data) > 1_000_000:
            return {
                "stdout": "",
                "stderr": "Output Limit Exceeded",
                "returncode": None,
                "killed_by_watchdog": False,
                "time_taken": (end_time - start_time) * 1000,
                "memory_taken": memory_used
            }

        return {
            "stdout": stdout_data,
            "stderr": stderr_data,
            "returncode": result.returncode,
            "killed_by_watchdog": False,
            "time_taken": (end_time - start_time) * 1000,
            "memory_taken": memory_used
        }

    except subprocess.TimeoutExpired:

        return {
            "stdout": "",
            "stderr": "TLE",
            "returncode": None,
            "killed_by_watchdog": True,
            "time_taken": time_limit,
            "memory_taken": None
        }


def compile_cpp(file_path: str):

    dir_path = os.path.dirname(os.path.abspath(file_path))
    file_name = os.path.basename(file_path)

    output_binary = file_name.replace(".cpp", ".out")

    result = subprocess.run(
        ["g++", file_name, "-O2", "-std=c++17", "-o", output_binary],
        cwd=dir_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=2
    )

    if result.returncode == 0:
        return {
            "success": True,
            "binary_name": output_binary,
            "stderr": result.stderr,
            "work_dir": dir_path
        }

    return {
        "success": False,
        "stderr": result.stderr
    }


def judge_against_testcases(command, submission, test_cases):

    if not test_cases:
        return {
            "verdict": "No Test Cases",
            "time_taken": 0,
            "memory_taken": 0
        }

    max_time = 0
    max_memory = 0

    work_dir = os.path.dirname(os.path.abspath(submission.file_path))

    for test_case in test_cases:

        result = run_code(
            command,
            test_case.input_data,
            submission.problem.time_limit,
            submission.problem.memory_limit,
            work_dir
        )

        if result["time_taken"] is not None:
            max_time = max(max_time, result["time_taken"])

        if result["memory_taken"] is not None:
            max_memory = max(max_memory, result["memory_taken"])

        if result["killed_by_watchdog"]:
            return {
                "verdict": "TLE",
                "time_taken": max_time,
                "memory_taken": max_memory
            }

        if result["returncode"] != 0:
            return {
                "verdict": "RUNTIME_ERROR",
                "time_taken": max_time,
                "memory_taken": max_memory
            }

        if result["stdout"].strip() != test_case.expected_output.strip():
            return {
                "verdict": "WRONG_ANSWER",
                "time_taken": max_time,
                "memory_taken": max_memory
            }

    return {
        "verdict": "ACCEPTED",
        "time_taken": max_time,
        "memory_taken": max_memory
    }