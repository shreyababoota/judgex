from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.utils.state_machine import update_status
from app.models import User, Submission, Problem
from app.extentions import db
from app.utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/promote/<int:user_id>", methods=["POST"])
@jwt_required()
@admin_required
def promote_user(user_id):
    user = db.session.get(User, user_id)

    if not user:
        return {"error": "User not found"}, 404

    if user.role == "ADMIN":
        return {"error": "User is already an admin"}, 400

    user.role = "ADMIN"
    db.session.commit()

    return {"message": f"User {user.email} promoted to admin successfully"}, 200


@admin_bp.route("/admin/rejudge/<int:submission_id>", methods=["POST"])
@jwt_required()
@admin_required
def rejudge_submission(submission_id):

    submission = db.session.get(Submission, submission_id)

    if not submission:
        return {"error": "Submission not found"}, 404

    if submission.status not in {"DONE", "ERROR"}:
        return {"error": "Only submissions with status DONE or ERROR can be rejudged"}, 400

    submission.verdict = None
    submission.time_taken = None
    submission.memory_taken = None

    update_status(submission, "IN_QUEUE")

    db.session.commit()

    return {"message": "Submission requeued for judging"}, 200


@admin_bp.route("/admin/submissions", methods=["GET"])
@jwt_required()
@admin_required
def admin_list_submissions():

    submissions = Submission.query.order_by(
        Submission.submitted_at.desc()
    ).limit(100).all()

    result = [
        {
            "id": s.id,
            "user_id": s.user_id,
            "problem_id": s.problem_id,
            "language": s.language,
            "status": s.status,
            "verdict": s.verdict,
            "submitted_at": s.submitted_at.isoformat()
        }
        for s in submissions
    ]

    return {"submissions": result}, 200

@admin_bp.route("/admin/users", methods=["GET"])
@jwt_required()
@admin_required
def list_users():

    users = User.query.order_by(User.id.asc()).all()

    result = [
        {
            "id": u.id,
            "email": u.email,
            "role": u.role
        }
        for u in users
    ]

    return {"users": result}, 200

@admin_bp.route("/admin/problem/<int:problem_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_problem(problem_id):

    problem = db.session.get(Problem, problem_id)

    if not problem:
        return {"error": "Problem not found"}, 404

    db.session.delete(problem)
    db.session.commit()

    return {"message": "Problem deleted successfully"}