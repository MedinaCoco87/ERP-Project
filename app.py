import os

from cs50 import SQL
from flask import Flask, jsonify, redirect, request
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash


# Configuring flask app
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

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


@app.route ("/customers/<customer_id>", methods = ["PUT"])
def update_customer(customer_id):
    customer_new_data = request.get_json()
    for key in customer_new_data:
        db.execute("UPDATE customers SET ? = ? WHERE id = ?", key, customer_new_data[key], customer_id)

    return jsonify({"message": "user updated"}), 200

@app.route("/customers/<customer_id>", methods = ["GET"])
def get_customer_by_id(customer_id):
    customer = db.execute("SELECT * FROM customers WHERE id = ?", customer_id)
    if not customer:
        return jsonify({"message": "customer not found"}), 400
    return jsonify(customer), 200
    

@app.route("/customers/", methods = ["GET"])
def get_customer_by_name():
    get_the_name = request.get_json()
    customers = db.execute("SELECT * FROM customers WHERE company_name LIKE ?", ('%'+get_the_name["company_name"]+'%'))
    if not customers:
        return jsonify({"message": "customer not found"}), 400
    return jsonify(customers), 200


# Database is validating category_id is an integer between 100 and 999.
@app.route ("/item_categories", methods = ["POST"])
def create_category():
    category = request.get_json()
    db.execute("INSERT INTO item_categories (id, description) VALUES (?, ?)", category["id"], category["description"].upper())
    return jsonify({"message": "item_category created"})


if __name__ == "__main__":
    app.run(debug=True)


