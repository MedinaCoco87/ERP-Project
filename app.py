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

@app.route ("/user", methods = ["POST"])
def create_user():
    user = request.get_json()
    db.execute ("INSERT INTO users (username, hashed_pass, profile, status) VALUES (?, ?, ?, ?)", user["username"], user["password"], user["profile"], user["status"])
    return jsonify({"message": "user created"})

@app.route ("/user/<user_id>", methods = ["GET"])
def get_user_by_id():
    pass
