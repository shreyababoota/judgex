import subprocess
import os
import uuid

def run_code_docker(file_path: str, command: str, input_data: str, time_limit: int, memory_limit: int):
    file_name = os.path.basename(file_path)
    dir_path = os.path.dirname(os.path.abspath(file_path))

    memory_limit_str = f"{memory_limit}m"
    container_name = f"judge_{uuid.uuid4().hex}"

    command = f"""
/usr/bin/time -f '%e'{command}
echo __MEMORY__
if [ -f /sys/fs/cgroup/memory.peak ]; then
    cat /sys/fs/cgroup/memory.peak
elif [ -f /sys/fs/cgroup/memory.max_usage_in_bytes ]; then
    cat /sys/fs/cgroup/memory.max_usage_in_bytes
elif [ -f /sys/fs/cgroup/memory.current ]; then
    cat /sys/fs/cgroup/memory.current
fi
"""

    cmd = [
        "docker", "run",
        "--rm",
        "-i",
        "--name", container_name,
        "--memory", memory_limit_str,
        "--cpus", "1",
        "--network", "none",
        "--pids-limit", "64",
        "--cap-drop", "ALL",
        "-v", f"{dir_path}:/app",
        "-w", "/app",
        "judge-base",
        "sh", "-c", command
    ]

    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # outer watchdog timeout
        outer_timeout_seconds = (time_limit / 1000) + 1

        stdout_data, stderr_data = process.communicate(
            input=input_data,
            timeout=outer_timeout_seconds
        )

        # Parse memory usage
        memory_taken = None

        if "__MEMORY__" in stdout_data:
            parts = stdout_data.splitlines()
            marker_index = parts.index("__MEMORY__")

            if marker_index + 1 < len(parts):
                try:
                    memory_taken = int(parts[marker_index + 1])
                except ValueError:
                    memory_taken = None

            stdout_data = "\n".join(parts[:marker_index])

        # Parse execution time
        time_taken = None
        clean_stderr = ""

        if stderr_data:
            lines = stderr_data.strip().splitlines()
            last_line = lines[-1]

            try:
                # convert seconds → ms
                time_taken = float(last_line) * 1000
                clean_stderr = "\n".join(lines[:-1])
            except ValueError:
                clean_stderr = stderr_data

        # prevent huge output abuse
        if len(stdout_data) > 1_000_000:
            return {
                "stdout": "",
                "stderr": "Output Limit Exceeded",
                "killed_by_watchdog": False,
                "returncode": None,
                "time_taken": time_taken,
                "memory_taken": memory_taken
            }

        return {
            "stdout": stdout_data,
            "stderr": clean_stderr,
            "killed_by_watchdog": False,
            "returncode": process.returncode,
            "time_taken": time_taken,
            "memory_taken": memory_taken
        }

    except subprocess.TimeoutExpired:
        subprocess.run(
            ["docker", "kill", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {
            "stdout": "",
            "stderr": "TLE",
            "killed_by_watchdog": True,
            "returncode": None,
            "time_taken": time_limit,
            "memory_taken": None
        }

def compile_cpp_docker(file_path: str, memory_limit: int):
    file_name=os.path.basename(file_path)
    dir_path=os.path.dirname(os.path.abspath(file_path))

    memory_limit_str=f"{memory_limit}m"
    container_name=f"judge_compile_{uuid.uuid4().hex}"
    output_binary=file_name.replace(".cpp", ".out")
    command=f"g++ {file_name} -o {output_binary}"

    cmd = [
        "docker", "run",
        "--rm",
        "--name", container_name,
        "--memory", memory_limit_str,
        "--cpus", "1",
        "--network", "none",
        "--pids-limit", "64",
        "--cap-drop", "ALL",
        "-v", f"{dir_path}:/app",
        "-w", "/app",
        "judge-base",
        "sh", "-c", command
    ]

    result=subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode == 0:
        return {
            "success": True,
            "stderr":result.stderr,
            "returncode": 0
        }
    else:
        return {
            "success": False,
            "binary_name": output_binary,
            "stderr": result.stderr,
            "returncode": result.returncode
        }



# Judge against testcases
def judge_against_testcases(submission, test_cases):
    if not test_cases:
        return {
            "verdict": "No Test Cases",
            "time_taken": 0,
            "memory_taken": 0
        }

    max_time = 0
    max_memory = 0

    for test_case in test_cases:
        result = run_python_code_docker(
            submission.file_path,
            test_case.input_data,
            submission.problem.time_limit,
            submission.problem.memory_limit
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

        if (result["time_taken"] is not None and
                result["time_taken"] > submission.problem.time_limit):
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