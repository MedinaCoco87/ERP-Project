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

@app.route ("/users", methods = ["POST"])
def create_user():
    user = request.get_json()
    db.execute ("INSERT INTO users (username, hashed_pass, profile, status) VALUES (?, ?, ?, ?)", user["username"], user["password"], user["profile"], user["status"])
    return jsonify({"message": "user created"})


@app.route ("/users", methods = ["GET"])
def get_all_users():
    users = db.execute("SELECT * FROM users")
    if not users:
        return jsonify({"message": "user not found"}), 400
    return jsonify(users), 200


@app.route ("/users/<user_id>", methods = ["GET"])
def get_user_by_id(user_id):
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    if not user:
        return jsonify({"message": "user not found"}), 400
    return jsonify(user), 200

# I intentionally choose not to allow deletion of users to avoid messing up with databases.

@app.route ("/customers", methods = ["POST"])
def create_customer():
    customer = request.get_json()
    db.execute(
        "INSERT INTO customers (company_name, tax_id, address_street, address_city, \
                address_country, payment_condition, credit_line) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                customer["company_name"], customer["tax_id"], customer["address_street"], 
                customer["address_city"], customer["address_country"], customer["payment_condition"],
                customer["credit_line"]
                )
    return jsonify({"message": "customer created"})

