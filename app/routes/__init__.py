from .auth import auth_bp
from .submissions import submissions_bp 
from .problems import problems_bp
from .frontend import frontend_bp

def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(submissions_bp)
    app.register_blueprint(problems_bp)
    app.register_blueprint(frontend_bp)

    