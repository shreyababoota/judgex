from .extentions import db
from flask import Flask
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role= db.Column(db.String(20), default="USER", nullable=False)

class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    statement = db.Column(db.Text, nullable=False)
    constraints= db.Column(db.Text, nullable=False)
    input_format = db.Column(db.Text, nullable=False)
    output_format = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)
    time_limit = db.Column(db.Integer, nullable=False)
    memory_limit = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.relationship("User", backref="problems")
    test_cases=db.relationship("TestCase", backref="problem", lazy=True)

class TestCase(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=False)
    input_data = db.Column(db.Text, nullable=False)
    expected_output = db.Column(db.Text, nullable=False)
    order_index = db.Column(db.Integer, nullable=False)
    is_hidden = db.Column(db.Boolean, default=True)

class Submission(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    user_id= db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=False)
    language= db.Column(db.String(50), nullable=False)
    verdict= db.Column(db.String(50), nullable=True)
    time_taken= db.Column(db.Float, nullable=True)
    memory_taken= db.Column(db.Integer, nullable=True)
    submitted_at= db.Column(db.DateTime, default=db.func.current_timestamp())
    status= db.Column(db.String(50), nullable=True)
    problem = db.relationship("Problem", backref="submissions")
    file_path= db.Column(db.String(255), nullable=True)
