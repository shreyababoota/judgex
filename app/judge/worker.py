import time
import os
from app.utils.state_machine import update_status
from app.extentions import db
from app.models import Submission, Problem, TestCase
from app.judge.code_runner import judge_against_testcases, compile_cpp
from app.judge.file_storage import BASE_STORAGE_DIR


def process_submission(submission):

    try:

        problem = Problem.query.get(submission.problem_id)

        test_cases = (
            TestCase.query
            .filter_by(problem_id=submission.problem_id)
            .order_by(TestCase.order_index.asc())
            .all()
        )

        # reconstruct full path from stored file_name
        file_path = os.path.join(BASE_STORAGE_DIR, submission.file_name)

        # ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # ALWAYS recreate file from DB
        if submission.code:
            with open(file_path, "w") as f:
                f.write(submission.code)
        else:
            print("CODE MISSING FOR SUBMISSION:", submission.id)

            submission.verdict = "SYSTEM_ERROR"
            update_status(submission, "ERROR")
            db.session.commit()
            return

        file_name = os.path.basename(file_path)
        work_dir = os.path.dirname(os.path.abspath(file_path))

        # ---------------- LANGUAGE HANDLING ----------------

        if submission.language == "python":

            command = ["python3", file_name]

        elif submission.language == "cpp":

            compile_result = compile_cpp(file_path)

            if not compile_result["success"]:

                submission.verdict = "COMPILE_ERROR"
                update_status(submission, "DONE")
                db.session.commit()
                return

            binary_name = compile_result["binary_name"]

            command = ["./" + binary_name]

        else:

            submission.verdict = "SYSTEM_ERROR"
            update_status(submission, "ERROR")
            db.session.commit()
            return

        print(f"Processing submission {submission.id} with command {command}")

        # ---------------- RUN JUDGE ----------------

        result = judge_against_testcases(command, submission, test_cases)

        submission.verdict = result["verdict"]
        submission.time_taken = int(result["time_taken"] or 0)
        submission.memory_taken = int(result["memory_taken"] or 0)

        update_status(submission, "DONE")

    except Exception as e:

        print(f"Error processing submission {submission.id}: {e}")

        submission.verdict = "SYSTEM_ERROR"

        try:
            update_status(submission, "ERROR")
        except Exception:
            submission.status = "ERROR"

    finally:

        db.session.commit()


def run_worker(app, stop_event):

    print("WORKER STARTED")

    with app.app_context():

        # reset stuck submissions
        stuck = Submission.query.filter_by(status="RUNNING").count()
        if stuck:
            print(f"Resetting {stuck} stuck submissions")

        Submission.query.filter_by(status="RUNNING").update({"status": "IN_QUEUE"})
        db.session.commit()

        while not stop_event.is_set():

            candidate = (
                Submission.query
                .filter_by(status="IN_QUEUE")
                .order_by(Submission.submitted_at.asc())
                .first()
            )

            if candidate:

                rows_updated = (
                    Submission.query
                    .filter_by(id=candidate.id, status="IN_QUEUE")
                    .update({"status": "RUNNING"})
                )

                db.session.commit()

                if rows_updated == 1:

                    submission = Submission.query.get(candidate.id)

                    try:
                        process_submission(submission)

                    except Exception as e:
                        print("Worker error:", e)
                        submission.status = "SYSTEM_ERROR"
                        db.session.commit()

                    finally:
                        db.session.remove()

                else:
                    time.sleep(0.1)

            else:
                time.sleep(0.5)