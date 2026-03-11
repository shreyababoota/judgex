import time
from app import create_app
from app.utils.state_machine import update_status
from app.extentions import db
from app.models import Submission, Problem, TestCase
from app.judge.code_runner import judge_against_testcases, compile_cpp_docker
import os

def process_submission(submission):
    try:
        problem = Problem.query.get(submission.problem_id)
        test_cases = (
            TestCase.query
            .filter_by(problem_id=submission.problem_id)
            .order_by(TestCase.order_index.asc())
            .all()
        )

        file_path=submission.file_path
        file_name=os.path.basename(file_path)

        if submission.language=="python":
            command=f"python3 {file_name}"

        elif submission.language=="cpp":
            compile_result=compile_cpp_docker(file_path,submission.problem.memory_limit)
            print("COMPILER STDERR:", compile_result["stderr"])
            if not compile_result["success"]:
                submission.verdict="COMPILE_ERROR"
                update_status(submission,"DONE")
                db.session.commit()
                return
                
            binary_name = compile_result["binary_name"]
            command = f"./{binary_name}"            
        print(f"Processing submission {submission.id} with command: {command}")
        
        result=judge_against_testcases(command,submission,test_cases)

        submission.verdict = result["verdict"]
        submission.time_taken = result["time_taken"]
        submission.memory_taken = result["memory_taken"]
        update_status(submission,"DONE")
    
    except Exception as e:
        print(f"Error processing submission {submission.id}: {e}")
        submission.verdict='SYSTEM_ERROR'
        try:
            update_status(submission,"ERROR")
        except ValueError:
            submission.status="ERROR"   
        
        
    finally:
        db.session.commit()


def run_worker():
    app=create_app()
    with app.app_context():
        Submission.query.filter_by(status="RUNNING").update({"status": "IN_QUEUE"})
        db.session.commit()
        while True:
            candidate=(
                Submission.query
                .filter_by(status="IN_QUEUE")
                .order_by(Submission.submitted_at.asc())
                .first()
            )
            if candidate:
                rows_updated=(
                    Submission.query.filter_by(id=candidate.id, status="IN_QUEUE")
                    .update({"status": "RUNNING"})
                )
                db.session.commit()
                if rows_updated==1:
                    submission=Submission.query.get(candidate.id)
                    process_submission(submission)
                    db.session.remove()
                else:
                    time.sleep(0.1)
                
            else:
                time.sleep(1)

if __name__ == "__main__":
    run_worker()
