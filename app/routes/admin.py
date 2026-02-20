from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.utils.state_machine import update_status
from app.models import User, Submission
from app.extentions import db
from app.utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/promote/<int:user_id>", methods=["POST"])
@jwt_required()
@admin_required
def promote_user(user_id):
    user=User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404
    if user.role=="ADMIN":
        return {"error": "User is already an admin"}, 400
    user.role="ADMIN"
    db.session.commit()
    return {"message": f"User {user.email} promoted to admin successfully"}, 200

@admin_bp.route("/admin/rejudge/<int:submission_id>", methods=["POST"])
@jwt_required()
@admin_required
def rejudge_submission(submission_id):
    submission=Submission.query.get(submission_id)
    if not submission:
        return {"error": "Submission not found"}, 404
    
    if submission.status not in{"DONE", "ERROR"}:
        return {"error": "Only submissions with status DONE or ERROR can be rejudged"}, 400
    
    submission.verdict=None
    submission.time_taken=None
    submission.memory_taken=None

    update_status(submission,"IN_QUEUE")
    db.session.commit()

    return {"message":"Submission requeued for judging"}, 200  