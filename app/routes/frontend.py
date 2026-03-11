from flask import Blueprint, render_template
from flask import Blueprint, render_template

frontend_bp = Blueprint("frontend", __name__)

@frontend_bp.route("/submissions-page")
def submissions_page():
    return render_template("submissions.html")

@frontend_bp.route("/problems-page")
def problems_page():
    return render_template("problems.html")

@frontend_bp.route("/problem-page/<int:problem_id>")
def problem_page(problem_id):
    return render_template("problem_detail.html", problem_id=problem_id)

@frontend_bp.route("/login-page")
def login_page():
    return render_template("login.html")

@frontend_bp.route("/admin-login")
def admin_login_page():
    return render_template("admin_login.html")

@frontend_bp.route("/profile-page")
def profile_page():
    return render_template("profile.html")

@frontend_bp.route("/admin-dashboard")
def admin_dashboard():
    return render_template("admin_dashboard.html")

@frontend_bp.route("/admin/create-problem")
def create_problem_page():
    return render_template("create_problem.html")

@frontend_bp.route("/admin/add-testcase")
def add_testcase_page():
    return render_template("add_testcase.html")

@frontend_bp.route("/admin/rejudge-page")
def rejudge_page():
    return render_template("rejudge.html")

@frontend_bp.route("/admin/submissions-page")
def admin_submissions_page():
    return render_template("admin_submissions.html")

@frontend_bp.route("/signup-page")
def signup_page():
    return render_template("signup.html")

@frontend_bp.route("/admin/users-page")
def users_page():
    return render_template("admin_dashboard.html")