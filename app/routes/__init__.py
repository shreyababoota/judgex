from .auth import auth_bp
from .frontend import frontend_bp
from .admin import admin_bp
from .problems import problems_bp
from .submissions import submissions_bp


def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(frontend_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(problems_bp)
    app.register_blueprint(submissions_bp)