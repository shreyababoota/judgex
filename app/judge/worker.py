import time
from app import create_app
from app.utils.state_machine import update_status
from app.extentions import db
from app.models import Submission, Problem, TestCase
from app.judge.code_runner import run_python_code, judge_against_testcases

def process_submission(submission):
    try:
        problem = Problem.query.get(submission.problem_id)
        test_cases = (
            TestCase.query
            .filter_by(problem_id=submission.problem_id)
            .order_by(TestCase.order_index.asc())
            .all()
        )

        result = judge_against_testcases(submission, test_cases)
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
                .order_by(Submission.created_at.asc())
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
