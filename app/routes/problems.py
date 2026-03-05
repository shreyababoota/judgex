from flask import Blueprint, request
from ..extentions import db
from ..models import Problem, User
from ..models import TestCase
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.decorators import admin_required

problems_bp = Blueprint("problems", __name__)

@problems_bp.route("/problems", methods=["POST"])
@jwt_required()
@admin_required
def create_problem():
    data=request.get_json()
    user_id=int(get_jwt_identity())

    if not data:
        return {"error": "No data provided"}, 400
    required_fields = ["title", "statement", "time_limit", "memory_limit","constraints","input_format","output_format","difficulty"]
    for field in required_fields:
        if field not in data:
            return {"error": f"Missing field: {field}"}, 400
    if not isinstance(data["time_limit"], int):
        return {"error": "Time limit must be integer"}, 400
    if data["time_limit"] <= 0:
        return {"error": "Time limit must be greater than 0"}, 400
    if not isinstance(data["memory_limit"], int):
        return {"error": "Memory limit must be integer"}, 400
    if data["memory_limit"] <= 0:
        return {"error": "Memory limit must be greater than 0"}, 400
    allowed_difficulties = ["easy", "medium", "hard"]
    if not isinstance(data["difficulty"], str):
        return {"error": "Difficulty must be a string"}, 400
    difficulty=data["difficulty"].strip().lower()
    if difficulty not in allowed_difficulties:
        return {"error": "Invalid difficulty. Must be easy, medium, or hard"}, 400
    problem=Problem(
        title=data["title"],
        statement=data["statement"],
        time_limit=data["time_limit"],
        memory_limit=data["memory_limit"],
        constraints=data["constraints"],
        input_format=data["input_format"],
        output_format=data["output_format"],
        difficulty=difficulty,
        created_by=user_id
    )
    db.session.add(problem)
    db.session.commit()
    return {"message": "Problem created successfully", "problem_id": problem.id}, 201

@problems_bp.route("/problems", methods=["GET"])
def list_problems():
    try:
        page=int(request.args.get("page", 1))
        limit=int(request.args.get("limit", 10))
    except ValueError:
        return {"error": "Page and limit must be integers"}, 400
    if page<=0:
        return {"error": "Page must be greater than 0"}, 400
    if limit<=0:
        return {"error": "Limit must be greater than 0"}, 400
    if limit>50:
        limit=50
    problems=(
        Problem.query
        .order_by(Problem.created_at.desc())
        .offset((page-1)*limit)
        .limit(limit)
        .all()
    )
    result=[
        {
            "id": p.id,
            "title": p.title,
            "difficulty": p.difficulty,
        }
        for p in problems
    ]
    return{
        "problems": result,
        "page": page,
        "limit": limit,
    },200

@problems_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    problem=Problem.query.get(problem_id)
    if not problem:
        return {"error": "Problem not found"}, 404
    return{
        "id": problem.id,
        "title":problem.title,
        "statement":problem.statement,
        "constraints":problem.constraints,
        "input_format":problem.input_format,
        "output_format":problem.output_format,
        "difficulty":problem.difficulty,
        "time_limit":problem.time_limit,
        "memory_limit":problem.memory_limit,
        "created_at":problem.created_at.isoformat(),
    }

@problems_bp.route("/problems/<int:problem_id>/testcases", methods=["POST"])
@jwt_required()
def add_test_case(problem_id):
    problem=Problem.query.get(problem_id)
    if not problem:
        return {"error": "Problem not found"}, 404
    user_id=int(get_jwt_identity())

    if problem.created_by!=user_id:
        return{"error":"Forbidden"},403
    data=request.get_json()
    if not data:
        return {"error": "No data provided"}, 400
    
    required_fields=["input_data", "expected_output", "order_index"]
    for field in required_fields:
        if field not in data:
            return {"error": f"Missing field: {field}"}, 400
        
    #validate required fields
    if not isinstance(data["input_data"], str):
        return {"error": "Input data must be a string"}, 400
    if not isinstance(data["expected_output"], str):
        return {"error": "Expected output must be a string"}, 400
    if not isinstance(data["order_index"], int):
        return {"error": "Order index must be an integer"}, 400
    
    if data["order_index"]<=0:
        return {"error": "Order index must be greater than zero"}, 400
    if not data["input_data"].strip():
        return {"error": "Input data cannot be empty"}, 400
    if not data["expected_output"].strip(): 
        return {"error": "Expected output cannot be empty"}, 400
    
    existing=TestCase.query.filter_by(
        problem_id=problem_id,
        order_index=data["order_index"]
    ).first()
    if existing:
        return {"error": "Test case with this order index already exists for this problem"}, 400
    
    is_hidden=data.get("is_hidden", True)
    if not isinstance(is_hidden, bool):
        return {"error": "is_hidden must be a boolean"}, 400
    
    input_data=data["input_data"].strip()
    expected_output=data["expected_output"].strip()
    order_index=data["order_index"]

    test_case=TestCase(
        problem_id=problem_id,
        input_data=input_data,
        expected_output=expected_output,
        order_index=order_index,
        is_hidden=is_hidden
    )
    db.session.add(test_case)
    db.session.commit()

    return{
        "message": "Test case added successfully",
        "test_case_id": test_case.id
    },201
