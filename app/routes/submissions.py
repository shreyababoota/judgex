import math
import os
import uuid
import subprocess

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.judge.file_storage import save_submission_file
from app.judge.code_runner import run_code, compile_cpp

from ..extentions import db
from ..models import Submission, Problem, User


submissions_bp = Blueprint("submissions", __name__)


# ---------------- CREATE SUBMISSION ----------------

@submissions_bp.route("/submissions", methods=["POST"])
@jwt_required()
def create_submission():

    data = request.get_json()

    allowed_languages = ["python", "cpp", "java"]

    if not data:
        return {"error": "Invalid input"}, 400

    required_fields = ["problem_id", "code", "language"]

    for field in required_fields:
        if field not in data:
            return {"error": f"Missing field: {field}"}, 400

    if not isinstance(data["problem_id"], int):
        return {"error": "Problem ID must be an integer"}, 400

    if not isinstance(data["code"], str):
        return {"error": "Code cannot be empty"}, 400

    if not isinstance(data["language"], str):
        return {"error": "Language must be a string"}, 400

    language = data["language"].strip().lower()
    code = data["code"].strip()
    problem_id = data["problem_id"]

    if language not in allowed_languages:
        return {"error": "Unsupported language"}, 400

    if not code:
        return {"error": "Code cannot be empty"}, 400

    if len(code) > 1000:
        return {"error": "Code length exceeds limit"}, 400

    problem = Problem.query.get(problem_id)

    if not problem:
        return {"error": "Problem not found"}, 404

    user_id = int(get_jwt_identity())

    submission = Submission(
    user_id=user_id,
    problem_id=problem_id,
    language=language,
    code=code,              # ← store code in DB
    status="IN_QUEUE",
    verdict=None
)

    db.session.add(submission)
    db.session.commit()

    try:

        file_path = save_submission_file(
            submission.id,
            code,
            language
        )

        submission.file_path = file_path
        db.session.commit()

    except Exception:
        db.session.delete(submission)
        db.session.commit()
        return {"error": "Failed to save submission file"}, 500

    return {
        "submission_id": submission.id,
        "status": submission.status,
    }, 201


# ---------------- GET SINGLE SUBMISSION ----------------

@submissions_bp.route("/submissions/<int:submission_id>", methods=["GET"])
@jwt_required()
def get_submission(submission_id):

    user_id = int(get_jwt_identity())

    submission = Submission.query.get_or_404(submission_id)

    if submission.user_id != user_id:
        return {"error": "Forbidden"}, 403

    code = submission.code

    # recreate file if missing
    if submission.file_path and not os.path.exists(submission.file_path):
        os.makedirs(os.path.dirname(submission.file_path), exist_ok=True)
        with open(submission.file_path, "w") as f:
            f.write(code)

    return {
        "id": submission.id,
        "problem_id": submission.problem_id,
        "code": code,
        "language": submission.language,
        "status": submission.status,
        "verdict": submission.verdict,
        "time_taken": submission.time_taken,
        "memory_taken": submission.memory_taken,
        "submitted_at": submission.submitted_at.isoformat()
    }, 200


# ---------------- LIST SUBMISSIONS (PAGINATION) ----------------

@submissions_bp.route("/submissions", methods=["GET"])
@jwt_required()
def list_submissions():

    user_id = int(get_jwt_identity())

    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return {"error": "Page and limit must be integers"}, 400

    if page < 1:
        return {"error": "Page must be greater than 0"}, 400

    if limit < 1:
        return {"error": "Limit must be greater than 0"}, 400

    if limit > 50:
        limit = 50

    base_query = Submission.query.filter_by(user_id=user_id)

    total = base_query.count()

    submissions = (
        base_query
        .order_by(Submission.submitted_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    result = [
        {
            "id": s.id,
            "problem_id": s.problem_id,
            "language": s.language,
            "status": s.status,
            "verdict": s.verdict,
            "time_taken": s.time_taken,
            "memory_taken": s.memory_taken,
            "submitted_at": s.submitted_at.isoformat(),
            "problem_title": s.problem.title
        }
        for s in submissions
    ]

    total_pages = math.ceil(total / limit)

    return {
        "submissions": result,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages
    }, 200


# ---------------- RUN CODE (CUSTOM INPUT) ----------------

@submissions_bp.route("/run", methods=["POST"])
@jwt_required()
def run_code_route():

    data = request.json

    code = data.get("code")
    language = data.get("language")
    input_data = data.get("input", "")

    if not code or not language:
        return {"error": "Missing code or language"}, 400

    run_dir = f"/tmp/run_{uuid.uuid4().hex}"
    os.makedirs(run_dir, exist_ok=True)

    if language == "python":

        file_path = os.path.join(run_dir, "main.py")

        with open(file_path, "w") as f:
            f.write(code)

        command = ["python3", "main.py"]

    elif language == "cpp":

        file_path = os.path.join(run_dir, "main.cpp")

        with open(file_path, "w") as f:
            f.write(code)

        compile_result = compile_cpp(file_path)

        if not compile_result["success"]:
            return {
                "stdout": "",
                "stderr": compile_result["stderr"]
            }

        binary_name = compile_result["binary_name"]

        command = ["./" + binary_name]

    else:
        return {"error": "Unsupported language"}, 400

    result = run_code(
        command=command,
        input_data=input_data,
        time_limit=2000,
        memory_limit=256,
        work_dir=run_dir
    )

    return {
        "stdout": result["stdout"],
        "stderr": result["stderr"]
    }


# ---------------- VIEW SUBMISSION CODE ----------------

@submissions_bp.route("/submission/<int:id>/code")
@jwt_required()
def get_submission_code(id):

    user_id = int(get_jwt_identity())

    submission = Submission.query.get_or_404(id)

    user = User.query.get(user_id)

    if submission.user_id != user_id and user.role != "ADMIN":
        return {"error": "Forbidden"}, 403

    code = submission.code

    if submission.file_path and not os.path.exists(submission.file_path):
        os.makedirs(os.path.dirname(submission.file_path), exist_ok=True)
        with open(submission.file_path, "w") as f:
            f.write(code)

    return jsonify({"code": code})

@submissions_bp.route("/submissions/<int:submission_id>/status", methods=["GET"])
@jwt_required()
def get_submission_status(submission_id):

    user_id = int(get_jwt_identity())

    submission = Submission.query.get_or_404(submission_id)

    if submission.user_id != user_id:
        return {"error": "Forbidden"}, 403

    return {
        "status": submission.status,
        "verdict": submission.verdict,
        "time_taken": submission.time_taken,
        "memory_taken": submission.memory_taken,
    }, 200