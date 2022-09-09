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
    db.execute("INSERT INTO customers (company_name, tax_id, address_street, address_city, address_country, payment_condition, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)", customer["company_name"], customer["tax_id"], customer["address_street"], customer["address_city"], customer["address_country"], customer["payment_condition"], customer["created_by"])
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
def get_customers_by_name():
    get_the_name = []
    if request.is_json:
        get_the_name = request.get_json()
        customers = db.execute("SELECT * FROM customers WHERE company_name LIKE ?", ('%'+get_the_name["company_name"]+'%'))
        if not customers:
            return jsonify({"message": "customer not found"}), 400
        return jsonify(customers), 200
    # In case user doesn't type any name will return all customers
    else:
        all_customers = db.execute("SELECT * FROM customers")
        if not get_the_name:
            return jsonify(all_customers), 200


# Database is validating category_id is an integer between 100 and 999.
@app.route ("/item_categories", methods = ["POST"])
def create_category():
    category = request.get_json()
    db.execute("INSERT INTO item_categories (id, description, created_by) VALUES (?, ?, ?)", category["id"], category["description"].upper(), category["created_by"])
    return jsonify({"message": "item_category created"})

@app.route ("/items", methods = ["POST"])
def create_item():
    # Get json from postman
    item = request.get_json()
    # Identify the category for the new item and get the category full row from its table.
    item_category_row = db.execute("SELECT * FROM item_categories WHERE id = ?", item["category_id"])
    # Get the counter from the category
    category_counter = item_category_row[0]["counter"]
    # Generate the item_id by concatenating category_id + category_id_counter
    item_id = int(str(item["category_id"]) + str(category_counter).zfill(4))
    # Insert new item into items table.
    db.execute("INSERT INTO items (id, description, full_description, category_id, status, created_by) VALUES (?, ?, ?, ?, ?, ?)", item_id, item["description"], item["full_description"], item["category_id"], item["status"], item["created_by"])
    # Update counter on item_categories
    category_counter = category_counter + 1
    db.execute("UPDATE item_categories SET counter = ? WHERE id = ?", category_counter, item["category_id"])
    return jsonify({"message": "item created", "item": item_id}), 200



if __name__ == "__main__":
    app.run(debug=True)


