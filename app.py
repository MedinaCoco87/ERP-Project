import os

from cs50 import SQL
from flask import Flask, jsonify, redirect, request
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash


# Configuring flask app
app = Flask(__name__)

# Configure database
db = SQL("sqlite:///erpdatabase.db")

# Initial routes to test from postman

@app.route ("/user", methods = ["POST"])
def create_user():
    user = request.get_json()
    db.execute ("INSERT INTO users (username, hashed_pass, profile, status) VALUES (?, ?, ?, ?)", user["username"], user["password"], user["profile"], user["status"])
    return jsonify({"message": "user created"})


@app.route ("/user", methods = ["GET"])
def get_all_users():
    users = db.execute("SELECT * FROM users")
    if not users:
        return jsonify({"message": "user not found"}), 400
    return jsonify(users), 200
    

@app.route ("/user/<user_id>", methods = ["GET"])
def get_user_by_id(user_id):
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    if not user:
        return jsonify({"message": "user not found"}), 400
    return jsonify(user), 200
