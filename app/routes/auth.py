from flask import request, Blueprint
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from ..extentions import db
from ..models import User
auth_bp= Blueprint("auth",__name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data=request.get_json()
    if not data:
        return {"error": "No data provided"}, 400
    if "email" not in data or "password" not in data:
        return {"error":"Both email and password are required"},400
    user=User.query.filter_by(email=data["email"]).first()
    if not user or not check_password_hash(user.password_hash,data["password"]):
        return {"error": "Invalid email or password"}, 401
    access_token=create_access_token(identity=str(user.id))
    return{
        "message": "Login successful",
        "access_token": access_token,
        "role": user.role
    },200

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data=request.get_json()
    if not data:
        return {"error": "No data provided"}, 400
    if "email" not in data or "password" not in data:
        return {"error":"Both email and password are required"},400
    
    user_count = User.query.count()
    email=data["email"].strip().lower()
    hashed_password = generate_password_hash(data["password"].strip())

    role = "ADMIN" if user_count == 0 else "USER"

    new_user = User(
        email=email,
        password_hash=hashed_password,
        role=role
    )
    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "Email already exists"}, 409
    return {"message": "User created successfully"}, 201

@auth_bp.route("/profile",methods=["GET"])
@jwt_required()
def profile():
    user_id=int(get_jwt_identity())
    user=User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 401
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
    },200
