from app.judge.code_runner import run_python_code_docker

code = "print(input())"
run_python_code_docker(code, "hello", 1000, 128)
