import subprocess
import os
import time
import signal


def run_code(command, input_data, time_limit, memory_limit, work_dir):

    start_time = time.perf_counter()

    try:
        wrapped_command = ["bash", "-c", f"/usr/bin/time -f 'MEM:%M' {' '.join(command)}"]

        process = subprocess.Popen(
            wrapped_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=work_dir,
            preexec_fn=os.setsid  # start new process group
        )

        try:
            stdout_data, stderr_data = process.communicate(
                input=(input_data + "\n") if not input_data.endswith("\n") else input_data,
                timeout=time_limit / 1000
            )
            import sys

            print("==== JUDGE DEBUG ====", flush=True)
            print("COMMAND:", wrapped_command, flush=True)
            print("STDOUT RAW:", repr(stdout_data), flush=True)
            print("STDERR RAW:", repr(stderr_data), flush=True)
            print("RETURN CODE:", process.returncode, flush=True)
            print("=====================", flush=True)

            sys.stdout.flush()

        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)

            return {
                "stdout": "",
                "stderr": "TLE",
                "returncode": None,
                "killed_by_watchdog": True,
                "time_taken": time_limit,
                "memory_taken": 0
            }

        # Extract memory usage from /usr/bin/time
        memory_kb = 0
        stderr_lines = stderr_data.splitlines()

        clean_stderr = []

        for line in stderr_lines:
            line = line.strip()

            if line.startswith("MEM:"):
                try:
                    memory_kb = int(line.split(":")[1])
                except:
                    memory_kb = 0
            else:
                clean_stderr.append(line)

        stderr_data = "\n".join(clean_stderr)

        end_time = time.perf_counter()

        runtime = int((end_time - start_time) * 1000)
        runtime = min(runtime, time_limit)

        if len(stdout_data) > 1_000_000:
            return {
                "stdout": "",
                "stderr": "Output Limit Exceeded",
                "returncode": None,
                "killed_by_watchdog": False,
                "time_taken": runtime,
                "memory_taken": memory_kb
            }

        # Memory limit check
        if memory_limit and memory_kb > memory_limit * 1024:
            return {
                "stdout": "",
                "stderr": "MLE",
                "returncode": None,
                "killed_by_watchdog": False,
                "time_taken": runtime,
                "memory_taken": memory_kb
            }

        return {
            "stdout": stdout_data,
            "stderr": stderr_data,
            "returncode": process.returncode,
            "killed_by_watchdog": False,
            "time_taken": runtime,
            "memory_taken": memory_kb
        }

    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": None,
            "killed_by_watchdog": False,
            "time_taken": 0,
            "memory_taken": 0
        }


def compile_cpp(file_path: str):

    dir_path = os.path.dirname(os.path.abspath(file_path))
    file_name = os.path.basename(file_path)

    output_binary = file_name.replace(".cpp", ".out")

    try:
        result = subprocess.run(
            ["g++", file_name, "-O2", "-std=c++17", "-o", output_binary],
            cwd=dir_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stderr": "Compilation timed out"
        }

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

    from app.judge.file_storage import BASE_STORAGE_DIR

    file_path = os.path.join(BASE_STORAGE_DIR, submission.file_name)
    work_dir = os.path.dirname(os.path.abspath(file_path))

    for test_case in test_cases:
        print("RUNNING TESTCASE:", submission.id, flush=True)

        result = run_code(
            command,
            test_case.input_data,
            submission.problem.time_limit,
            submission.problem.memory_limit,
            work_dir
        )

        max_time = max(max_time, result["time_taken"] or 0)
        max_memory = max(max_memory, result["memory_taken"] or 0)

        if result["killed_by_watchdog"]:
            return {
                "verdict": "TLE",
                "time_taken": max_time,
                "memory_taken": max_memory
            }

        if result["returncode"] not in (0, None):
            return {
                "verdict": "RUNTIME_ERROR",
                "time_taken": max_time,
                "memory_taken": max_memory
            }

        if result["stderr"] == "MLE":
            return {
                "verdict": "MLE",
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