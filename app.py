import warnings
warnings.filterwarnings('ignore')

import os

import json
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from auxiliary import login_required
from operator import itemgetter


# Configuring flask app
app = Flask(__name__)


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure database
db = SQL("sqlite:///erpdatabase.db")

# Configure Session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_COOKIE_NAME"] = "SESSION"
Session(app)

# Set global variables
tax_rate = 0.18
regular_profiles = ["standard", "admin"]
super_admin = "super_admin"

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods = ["GET"])
@login_required
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user info
    session.clear()
    if request.method == "GET":
        return render_template ("login.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", username
        )

        if len(user) != 1:
            return render_template("error.html", message="Invalid user")
        if not check_password_hash(user[0]["hashed_pass"], password):
            return render_template("error.html", message="Invalid password")

        session["user_id"] = user[0]["id"]
        session["username"] = user[0]["username"]
        session["profile"] = user[0]["profile"]
        session["message"] = ""
        return redirect("/")


@app.route("/logout", methods = ["GET"])
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


# Pending implementation
@app.route("/edit_user", methods = ["GET", "POST"])
@login_required
def edit_user(): # Allow super_admin to change other users passwords and profiles
    pass
        

@app.route("/change_password", methods = ["POST", "GET"])
def change_password():
    if request.method == "POST":
        user_current_info = db.execute(
            "SELECT * FROM users WHERE id = ?", session["user_id"] 
        )
        old_pass = request.form.get("old_password")
        new_pass = request.form.get("new_password")
        confirm_pass = request.form.get("confirm_password")
        if not old_pass or old_pass != user_current_info[0]["hashed_pass"]:
            return render_template("error.html", message="Invalid password")
        if not new_pass or not confirm_pass or new_pass != confirm_pass:
            return render_template("error.html", message="Password and/or confirmation are not valid")
        db.execute(
            "UPDATE users SET hashed_pass = ? WHERE id = ?",
            generate_password_hash(new_pass), session["user_id"]
        )
        return render_template("success.html", message="Password succesfully changed")
    
    return render_template("change_password.html")

    
# Test POST route for invalid inputs
@app.route ("/create_user", methods = ["GET", "POST"])
def create_user():
    if request.method == "POST":
        if session["profile"] == "admin":
            # Get the user input from the form:
            username = request.form.get("username").lower()
            plain_password = request.form.get("password")
            profile = request.form.get("profile")
            if profile not in regular_profiles:
                return render_template("error.html", message="invalid user profile")
            user_rows = db.execute(
                "SELECT * FROM users WHERE username = ?", username
            )
            if len(user_rows) == 1:
                return render_template("error.html", message="User already taken")
            if not plain_password:
                return render_template("error.html", message="Must provide a valid password")
            db.execute(
                "INSERT INTO users (username, hashed_pass, profile, status) VALUES (?, ?, ?, ?)",
                username, generate_password_hash(plain_password), profile, "active"
            )
            return redirect("/users")
        
        elif session["profile"] == super_admin:
            # Get the user input from the form:
            username = request.form.get("username").lower()
            plain_password = request.form.get("password")
            profile = request.form.get("profile")
            if session["profile"] not in [regular_profiles, super_admin]:
                return render_template("error.html", message="Invalid user profile")
            user_rows = db.execute(
                "SELECT * FROM users WHERE username = ?", username
            )
            if len(user_rows) == 1:
                return render_template("error.html", message="User already taken")
            if not plain_password:
                return render_template("error.html", message="Must provide a valid password")
            db.execute(
                "INSERT INTO users (username, hashed_pass, profile) VALUES (?, ?, ?)",
                username, generate_password_hash(plain_password), profile
            )
            return redirect("/users")
        else:
            return render_template("error.html", message="You don't have permission to perform this action")
    
    return render_template("new_user.html")
        

@app.route ("/users", methods = ["GET"])
@login_required
def get_all_users():
    users = db.execute("SELECT * FROM users")
    return render_template("users.html", users=users)

# Pending vinculation with frontend
@app.route ("/users/<user_id>", methods = ["GET"])
def get_user_by_id(user_id):
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    if not user:
        return jsonify({"message": "user not found"}), 400
    return jsonify(user), 200


@app.route ("/create_customer", methods = ["GET", "POST"])
def create_customer():
    if request.method == "POST":
        tax_id = request.form.get("tax_id")
        existing_customer = db.execute(
            "SELECT * FROM customers WHERE tax_id = ?", tax_id
        )
        if len(existing_customer) >= 1:
            message = "Tax id already used for customer " + existing_customer[0]["company_name"] 
            return render_template("error.html", message=message)
        db.execute("INSERT INTO customers (company_name, tax_id, address_street, address_city, address_country, payment_condition, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)", 
            request.form.get("company_name").upper(), request.form.get("tax_id"), request.form.get("address_street").upper(), request.form.get("address_city").upper(), request.form.get("address_country").upper(), 
            request.form.get("payment_condition").upper(), session["username"]
        )
        customers = db.execute("SELECT * FROM customers")
        return render_template("customers.html", message="Customer created!", customers=customers)

    return render_template("create_customer.html")


# Pending vinculation with frontend
@app.route ("/customers/<customer_id>", methods = ["PUT"])
def update_customer(customer_id):
    customer_new_data = request.get_json()
    for key in customer_new_data:
        db.execute("UPDATE customers SET ? = ? WHERE id = ?", key, customer_new_data[key], customer_id)

    return jsonify({"message": "user updated"}), 200


# Partial vinculation with frontend
@app.route("/customers/<customer_id>", methods = ["GET"])
def get_customer_by_id(customer_id):
    customer = db.execute("SELECT * FROM customers WHERE id = ?", customer_id)
    if not customer:
        return jsonify([{"message": "customer not found"}]), 400
    return jsonify(customer), 200
    

@app.route("/customers/", methods = ["GET"])
@login_required
def get_customers():
    customers = db.execute("SELECT * FROM customers")
    return render_template("customers.html", customers=customers)


# Database is validating category_id is an integer between 100 and 999.

@app.route ("/get_item_categories", methods = ["GET"])
def get_item_categories():
    categories = db.execute("SELECT * FROM item_categories")
    return render_template("item_categories.html", categories=categories)


@app.route ("/create_category", methods = ["GET", "POST"])
def create_category():
    if request.method == "POST":
        category = db.execute(
            "SELECT * FROM item_categories WHERE id = ?",
            request.form.get("category_id")
        )
        if len(category) >= 1:
            return render_template("error.html", message="Category ID already taken")
        db.execute("INSERT INTO item_categories (id, description, created_by) VALUES (?, ?, ?)", 
        request.form.get("category_id"), request.form.get("description").upper(), session["username"])
        categories = db.execute("SELECT * FROM item_categories")
        return render_template("item_categories.html", categories=categories, message="Category created!")
    return render_template("create_categories.html")

# Pending vinculation with frontend
@app.route ("/category_by_id/<item_category>", methods = ["GET"])
def get_category(item_category):
    category = db.execute("SELECT * FROM item_categories WHERE id = ?", item_category)
    return jsonify(category), 200

@app.route ("/get_items", methods = ["GET"])
def get_items():
    items = db.execute("SELECT * FROM items")
    return render_template("items.html", items=items)

@app.route ("/create_item", methods = ["GET", "POST"])
def create_item():
    if request.method == "POST":
        # Identify the category for the new item and get the category full row from its table.
        item_category_row = db.execute(
            "SELECT * FROM item_categories WHERE id = ?", 
            request.form.get("category_id")
        )
        if not item_category_row:
            return render_template("error.html", message="invalid category")
        # Get the counter from the category
        category_counter = item_category_row[0]["counter"]
        # Generate the item_id by concatenating category_id + category_id_counter
        item_id = int(str(request.form.get("category_id")) + str(str(category_counter).zfill(4)))
        # Insert new item into items table.
        db.execute(
            "INSERT INTO items (id, description, full_description, category_id, status, created_by) VALUES (?, ?, ?, ?, ?, ?)", 
            item_id, request.form.get("description"), request.form.get("full_description"), request.form.get("category_id"), "ACTIVE", session["username"]
        )
        # Update counter on item_categories
        category_counter = category_counter + 1
        db.execute(
            "UPDATE item_categories SET counter = ? WHERE id = ?", 
            category_counter, request.form.get("category_id")
        )
        items = db.execute("SELECT * FROM items")
        message = "Item created " + str(item_id) + "."
        return render_template("items.html", items=items, message=message)

    return render_template("create_item.html")



@app.route ("/items/<item_id>", methods = ["GET"])
def get_item_by_id(item_id):
    item = db.execute("SELECT * FROM items WHERE id = ?", item_id)
    if not item:
        return jsonify([{"messagge": "item not found"}]), 400
    return jsonify(item), 200



# Pending vinculation to frontend
@app.route ("/items_by_category/<category_id>", methods = ["GET"])
def get_items_by_category(category_id):
    items = db.execute("SELECT * FROM items WHERE category_id = ?", category_id)
    if not items:
        return jsonify({"message": "this category is empty"}), 400
    return jsonify(items), 200



@app.route("/get_quotes_list", methods = ["GET"])
def get_all_quotes():
    quotes = db.execute("SELECT * FROM quote_header ORDER BY quote_num DESC")
    return render_template("quotes_list.html", quotes=quotes)


@app.route("/quote_details", methods=["GET"])
def get_quote_details():
    quote_id = request.args.get("quote_num")
    if not quote_id:
        header = db.execute("SELECT * FROM quote_header WHERE quote_num = ?", session["temp_quote_num"])
        bodies = db.execute(
        "SELECT * FROM quote_body WHERE quote_num = ? ORDER BY line_ref", session["temp_quote_num"]
        )
    else:
        header = db.execute("SELECT * FROM quote_header WHERE quote_num = ?", quote_id)
        bodies = db.execute(
        "SELECT * FROM quote_body WHERE quote_num = ? ORDER BY line_ref", quote_id
    )
    if not header:
        return render_template("error.html", message="Header could not be found!")
    length = len(bodies)
    if header[0]["blocked"] != 0:
        message = "This quote is currently blocked by another user!!!"
        return render_template("quote_details.html", length=length, header=header, bodies=bodies, message=message)
    return render_template("quote_details.html", length=length, header=header, bodies=bodies)


# Pending implementation in frontend
@app.route ("/create_quote", methods = ["GET", "POST"])
def create_quote():
    if request.method == "POST":
        # Get the quote_lines from the frontend form
        data = request.form.get("data")
        if not data:
            return render_template("error.html", message="There was an unexpected error. Contact your admin")
        # Format the string into json
        quote_lines = json.loads(data)
        # Check the user has provided a valid customer_id:
        customer = db.execute(
            "SELECT * FROM customers WHERE id = ?", request.form.get("customer_id")
        )
        if not customer:
            return render_template("error.html", message="Customer not valid")
        # Get the list of current valid items to compare with inputs
        items_list = db.execute("SELECT * FROM items")
        items = []
        # Make a new list with only the items_id
        for i in range(len(items_list)):
            items.append(items_list[i]["id"])
        # Validate all user's line level inputs:
        for i in range((len(quote_lines))-1):
            if not quote_lines[i+1]["item"] or int(quote_lines[i+1]["item"]) not in items:
                message = "Invalid item in line " + str(i+1)
                return render_template("error.html", message=message)
            if not quote_lines[i+1]["quantity"] or int(quote_lines[i+1]["quantity"]) <= 0:
                message = "Invalid quantity in line " + str(i+1)
                return render_template("error.html", message=message)
            if not quote_lines[i+1]["list_price"] or float(quote_lines[i+1]["list_price"]) <= 0:
                message = "Invalid price in line " + str(i+1)
                return render_template("error.html", message=message)
        
        # Create quote_header table to generate the quote number
        db.execute(
            "INSERT INTO quote_header (customer_id, company_name, created_by) VALUES (?, ?, ?)",
            request.form.get("customer_id"), request.form.get("company_name"), session["username"]
        )
        # Get the quote number to use it in quote body
        last_header = db.execute("SELECT * FROM quote_header ORDER BY quote_num DESC LIMIT 1")
        quote_number = last_header[0]["quote_num"]
        # Loop through all lines of quote_lines and insert them into quote_body table
        for i in range((len(quote_lines))-1):
            net_price = round(float(quote_lines[i+1]["list_price"]) * (1 - float(quote_lines[i+1]["discount"])), 2)
            line_net_total =  net_price *  int(quote_lines[i+1]["quantity"])
            db.execute(
                "INSERT INTO quote_body (quote_num, line_ref, item_id, item_desc, quantity, list_price, discount, net_price, line_net_total, lead_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                quote_number, quote_lines[i+1]["line"], int(quote_lines[i+1]["item"]), quote_lines[i+1]["description"], int(quote_lines[i+1]["quantity"]), 
                float(quote_lines[i+1]["list_price"]), float(quote_lines[i+1]["discount"]), net_price, line_net_total, quote_lines[i+1]["lead_time"]
            )
        # Get the full total from body to update headers table
        full_net_total = db.execute(
            "SELECT SUM(line_net_total) FROM quote_body WHERE quote_num = ?", quote_number,
        )
        db.execute(
            "UPDATE quote_header SET total_net_value = ? WHERE quote_num = ?",
            full_net_total[0]["SUM(line_net_total)"], quote_number
        )
        
        # Show the list of all recently created quotes
        return redirect("/get_quotes_list")
    
    return render_template("new_quote.html")


@app.route("/edit_quote", methods=["GET", "POST"])
def edit_quote():
    if request.method == "POST": 
        # Will validate all user input as if this was a complete new quote
        # Validate quote_header info (reject edition for completely SOLD quotes)
        header = db.execute(
            "SELECT * FROM quote_header WHERE quote_num = ? AND company_name = ? AND customer_id = ? AND status != ?",
            request.form.get("quote_num"), request.form.get("company_name"), request.form.get("customer_id"), "SOLD"
        )
        if not header:
            return render_template("error.html", message="Unauthorized modification")
        data = request.form.get("data")
        if not data:
            return render_template("error.html", message="There was an unexpected error. Contact your admin")
        quote_lines = json.loads(data)
        # Check the user has provided a valid customer_id:
        customer = db.execute(
            "SELECT * FROM customers WHERE id = ?", request.form.get("customer_id")
        )
        if not customer:
            return render_template("error.html", message="Customer not valid")
        # Get the list of current valid items to compare with inputs
        items_list = db.execute("SELECT * FROM items")
        items = []
        # Make a new list with only the items_id
        for i in range(len(items_list)):
            items.append(items_list[i]["id"])
        # Validate all user's line level inputs:
        for i in range((len(quote_lines))-1):
            if not quote_lines[i+1]["item"] or int(quote_lines[i+1]["item"]) not in items:
                message = "Invalid item in line " + str(i+1)
                return render_template("error.html", message=message)
            if not quote_lines[i+1]["quantity"] or int(quote_lines[i+1]["quantity"]) <= 0:
                message = "Invalid quantity in line " + str(i+1)
                return render_template("error.html", message=message)
            if not quote_lines[i+1]["list_price"] or float(quote_lines[i+1]["list_price"]) <= 0:
                message = "Invalid price in line " + str(i+1)
                return render_template("error.html", message=message)
        # Remove all original lines from quote_body except the ones already SOLD
        db.execute(
            "DELETE FROM quote_body WHERE quote_num = ? AND status != ?", 
            request.form.get("quote_num"), "SOLD"
        )
        # Loop through all lines of quote_lines and insert them into quote_body table
        for i in range((len(quote_lines))-1):
            if quote_lines[i+1]["status"] == "SOLD":
                continue
            net_price = round(float(quote_lines[i+1]["list_price"]) * (1 - float(quote_lines[i+1]["discount"])), 2)
            line_net_total = net_price *  int(quote_lines[i+1]["quantity"])
            db.execute(
                "INSERT INTO quote_body (quote_num, line_ref, item_id, item_desc, quantity, list_price, discount, net_price, line_net_total, lead_time, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                request.form.get("quote_num"), quote_lines[i+1]["line"], int(quote_lines[i+1]["item"]), quote_lines[i+1]["description"], int(quote_lines[i+1]["quantity"]), 
                float(quote_lines[i+1]["list_price"]), float(quote_lines[i+1]["discount"]), net_price, line_net_total, quote_lines[i+1]["lead_time"], quote_lines[i+1]["status"]
            )
        
        # Update quote_header total_net_value
        full_net_total = db.execute(
            "SELECT SUM(line_net_total) FROM quote_body WHERE quote_num = ?",
            request.form.get("quote_num")
        )
        # Update quote_header total_net_value and user
        db.execute(
            "UPDATE quote_header SET total_net_value = ?, created_by = ? WHERE quote_num = ?",
            full_net_total[0]["SUM(line_net_total)"], session["username"], request.form.get("quote_num")
        )
        
        # Unblock the quote to allow further modifications
        db.execute(
            "UPDATE quote_header SET blocked = ? WHERE quote_num = ?",
            int(0), request.form.get("quote_num")
        )

        # Send the user to the detail of the current quote
        session["temp_quote_num"] = request.form.get("quote_num")
        return redirect("/quote_details")

    if request.method == "GET":
        # Get the header from the quote. Forbid edits on fully SOLD quotes.
        header = db.execute(
            "SELECT * FROM quote_header WHERE quote_num = ? AND status != ?", 
            request.args.get("quote_num"), "SOLD"
        )
        if not header:
            return render_template("error.html", message="Error on selected quote")
        # Dont allow edits when quote is already blocked.
        if header[0]["blocked"] != 0:
            # Send the user back to the detail of the quote
            session["temp_quote_num"] = request.args.get("quote_num")
            return redirect("/quote_details") 
        db.execute(
            "UPDATE quote_header SET blocked = ? WHERE quote_num = ?",
            int(1), int(request.args.get("quote_num"))
        )
        bodies = db.execute(
            "SELECT * FROM quote_body WHERE quote_num = ?", request.args.get("quote_num")
        )
        return render_template("edit_quote.html", header=header, bodies=bodies)


@app.route("/unlock_quote", methods = ["POST"])
def unlock_quote():
    full_json = request.get_json()
    if not full_json:
        return render_template("error.html", message="Quote remained blocked. Contact your admin")
    quote_number = int(full_json["quote_num"])
    # Check the quote still exists
    quote_header = db.execute(
        "SELECT * FROM quote_header WHERE quote_num = ?", quote_number
    )
    if not quote_header:
        return jsonify({"message": "quote no longer exists"})
    db.execute(
        "UPDATE quote_header SET blocked = ? WHERE quote_num = ?",
        int(0), int(quote_number)
    )
    return jsonify({"message": "quote release succesfull"})



@app.route("/delete_quote", methods=["GET", "POST"])
def delete_quote():
    if request.method == "GET":
        # Get the header from the quote. Forbid deletes on fully SOLD quotes.
        header = db.execute(
            "SELECT * FROM quote_header WHERE quote_num = ? AND status != ?", 
            request.args.get("quote_num"), "SOLD"
        )
        if not header:
            return render_template("error.html", message="Cannot delete selected quote")
        # Dont allow edits when quote is already blocked.
        if header[0]["blocked"] != 0:
            # Send the user back to the detail of the quote
            session["temp_quote_num"] = request.args.get("quote_num")
            return redirect("/quote_details")
        # If the quote is not blocked, proceed to block it for current user
        db.execute(
            "UPDATE quote_header SET blocked = ? WHERE quote_num = ?",
            int(1), int(request.args.get("quote_num"))
        )
        bodies = db.execute(
        "SELECT * FROM quote_body WHERE quote_num = ? ORDER BY line_ref", int(request.args.get("quote_num"))
        )
        length = len(bodies)
        return render_template("delete_quote.html", length=length, header=header, bodies=bodies)

    if request.method == "POST":
        # Validate quote_num with customer_id and with total_net_value
        quote_header = db.execute(
            "SELECT * FROM quote_header WHERE quote_num = ? AND customer_id = ? AND status = ? AND total_net_value = ?",
            request.form.get("quote_num"), request.form.get("customer_id"), "PENDING", request.form.get("total_net_value")
        )
        if not quote_header:
            return render_template("error.html", message="You cannot delete this quote")
        # Delete quote from table quote_header
        db.execute(
            "DELETE FROM quote_body WHERE quote_num = ?", request.form.get("quote_num")
        )
        # Delete quote from table quote_body
        db.execute(
            "DELETE FROM quote_header WHERE quote_num = ?", request.form.get("quote_num")
        )
        return redirect("/get_quotes_list")




# Pending implementation in frontend
@app.route("/get_quote_by_id/<quote_id>", methods = ["GET"])
def get_quote_by_id(quote_id):
    quote_header = db.execute("SELECT * FROM quote_header WHERE quote_num = ?", quote_id)
    quote_body = db.execute ("SELECT * FROM quote_body WHERE quote_num = ?", quote_id)
    full_quote = jsonify({"quote_header": quote_header}, {"quote_body": quote_body})
    return full_quote



# Pending implementation in frontend
@app.route("/get_quotes_by_customerId/<customer_id>", methods = ["GET"])
def get_quotes_by_customer(customer_id):
    # Get all the quote_headers for this customer
    quote_headers = db.execute("SELECT * FROM quote_header WHERE customer_id = ?", customer_id)
    # Get me an empty list to store all the quotes as dictionaries
    quotes = []
    # For each quote_num in header, get me all the body rows with that same quote_num
    for i in range(len(quote_headers)):
        quote_body = db.execute("SELECT * FROM quote_body WHERE quote_num = ?", quote_headers[i]["quote_num"])
        quotes.append({"1_quote_header": quote_headers[i], "2_quote_body": quote_body})
    return jsonify(quotes)




# Pending full implementation
# I have to modify the quote_header table to include a company_name column
@app.route("/get_quotes_by_customer_name", methods = ["GET"])
def get_quotes_by_customer_name():
        # Check first if customer provides an input
    user_input = []
    if request.is_json:
        user_input = request.get_json()
        matching_customers_id = db.execute("SELECT id FROM customers WHERE company_name LIKE ?", ('%'+user_input["company_name"]+'%'))
        if not matching_customers_id:
            return jsonify({"message": "customer not found"}), 400
        print(matching_customers_id)
        return jsonify({"message": "ok"})
    else:
        return jsonify({"message": "must provide body"})


# For cases with several lines with same item, same quote_num & status PENDING...
# ...users will have to consider max quantity per line, the ones of the quote_body in each line.
# If users try to add up the lines and register them as one, will get exceeds quantity error.
# If same items were quoted in several lines, keep it the same for the sorder or edit the quote 1st.
@app.route("/convert_quote_to_sorder", methods = ["GET", "POST"])
def convert_quote_to_sorder(): 
    if request.method == "GET":
        # Get the header from the quote. Forbid edits on fully SOLD quotes.
        header = db.execute(
            "SELECT * FROM quote_header WHERE quote_num = ? AND status != ?", 
            request.args.get("quote_num"), "SOLD"
        )
        if not header:
            return render_template("error.html", message="Error on selected quote")
        # Dont allow convertions when quote is already blocked.
        if header[0]["blocked"] != 0:
            # Send the user back to the detail of the quote
            session["temp_quote_num"] = request.args.get("quote_num")
            return redirect("/quote_details") 
        db.execute(
            "UPDATE quote_header SET blocked = ? WHERE quote_num = ?",
            int(1), int(request.args.get("quote_num"))
        )
        bodies = db.execute(
            "SELECT * FROM quote_body WHERE quote_num = ? AND status = ?", 
            request.args.get("quote_num"), "PENDING"
        )

        # Show the form with all data from the quote preloaded
        return render_template("create_sorder.html", header=header, bodies=bodies)
    
    if request.method == "POST":

        # Get the data provided by user
        data = request.form.get("data")
        if not data:
            return render_template("error.html", message="There was an unexpected error. Contact your admin")
        sorder_lines = json.loads(data)

        # Check there is a quote_header row that matches both customer_id and quote_num
        quote_header = db.execute(
            "SELECT * FROM quote_header WHERE quote_num = ? AND customer_id = ?",
            int(sorder_lines[1]["quote_num"]), request.form.get("customer_id"))
        if not quote_header:
            return render_template("error.html", message="invalid quote number or customer id")
        
        # Checks item_id, pending quantity and lead_time(hidden from user) are valid for all sorder_lines
        # Multiple quotes to one sorder not allowed in this version of the program.
        for i in range((len(sorder_lines)) - 1):
            quote_lines = db.execute(
                "SELECT * FROM quote_body WHERE quote_num = ? AND item_id = ? AND net_price = ? AND lead_time = ? AND status = ?",
                int(sorder_lines[1]["quote_num"]), int(sorder_lines[i + 1]["item_id"]), float(sorder_lines[i + 1]["net_price"]), 
                sorder_lines[i + 1]["lead_time"], "PENDING"
            )
            if not quote_lines:
                message = "No pending line that matches your request for item " + str(sorder_lines[i + 1]["item_id"]) + "." 
                return render_template("error.html", message=message)
            # Making sure the program considers all lines that matches the query
            for j in range(len(quote_lines)):
                if int(quote_lines[j]["quantity"]) >= int(sorder_lines[i + 1]["quantity"]):
                    break
                if j == (len(quote_lines) - 1):
                    message = "No quote line with enough pending quantity for item " + str(sorder_lines[i + 1]["item_id"]) + "."
                    return render_template("error.html", message=message)

            
        # Create sorder_header
        db.execute(
            "INSERT INTO sorder_header (customer_id, company_name, created_by) VALUES (?, ?, ?)", 
            int(request.form.get("customer_id")), request.form.get("company_name"), session["username"]
        )
        # Get the sorder_header just created to use the order_num in the sorder_body
        sorder_header = db.execute(
            "SELECT * FROM sorder_header ORDER BY order_num DESC LIMIT 1"
        )
        if not sorder_header:
            return render_template("error.html", message="Fatal error while creating sorder_body")
        
        # Create the sorder_body and update stock table
        for i in range(len(sorder_lines)- 1):
            net_price = float(sorder_lines[i + 1]["list_price"]) * (1 - float(sorder_lines[i + 1]["discount"]))
            line_net_total = net_price * int(sorder_lines[i + 1]["quantity"])
            db.execute(
                "INSERT INTO sorder_body (order_num, line_ref, item_id, item_desc, quantity, list_price, discount, net_price, line_net_total, lead_time, delivery_date, status, po_number, quote_num) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                int(sorder_header[0]["order_num"]), int(sorder_lines[i + 1]["line_ref"]), int(sorder_lines[i + 1]["item_id"]),
                sorder_lines[i + 1]["description"], int(sorder_lines[i + 1]["quantity"]), float(sorder_lines[i + 1]["list_price"]), 
                float(sorder_lines[i + 1]["discount"]), net_price, line_net_total, int(sorder_lines[i + 1]["lead_time"]), 
                sorder_lines[i + 1]["delivery_date"], "PENDING", sorder_lines[i + 1]["po_num"], int(sorder_lines[i + 1]["quote_num"])
            )
            item_stocks = db.execute(
                "SELECT * FROM stock WHERE item_id = ?", int(sorder_lines[i + 1]["item_id"])
            )
            new_onsale = item_stocks[0]["stock_onsale"] + int(sorder_lines[i + 1]["quantity"])
            new_available = item_stocks[0]["stock_available"] - int(sorder_lines[i + 1]["quantity"])
            db.execute(
                "UPDATE stock SET stock_onsale = ?, stock_available = ? WHERE item_id = ?",
                new_onsale, new_available, int(sorder_lines[i + 1]["item_id"])
            )

        # Update sorder_header total_net_value
        full_net_total = db.execute(
            "SELECT SUM(line_net_total) FROM sorder_body WHERE order_num = ?",
            sorder_header[0]["order_num"]
        )
        db.execute(
            "UPDATE sorder_header SET total_net_value = ? WHERE order_num = ?",
            full_net_total[0]["SUM(line_net_total)"], sorder_header[0]["order_num"]
        )

        # Update status of quote_body lines involved to "sold"
        for i in range(len(sorder_lines)- 1):
            perfect_match = db.execute(
                "SELECT * FROM quote_body WHERE quote_num = ? AND line_ref = ? AND item_id = ? AND quantity = ? AND net_price = ? AND status = ? AND lead_time = ?",
                int(sorder_lines[i + 1]["quote_num"]), int(sorder_lines[i + 1]["line_ref"]), int(sorder_lines[i + 1]["item_id"]), 
                int(sorder_lines[i + 1]["quantity"]), float(sorder_lines[i + 1]["net_price"]), "PENDING",
                int(sorder_lines[i + 1]["lead_time"])
            )
            # if there is a perfect match, just update the first line and go to next iteration
            if perfect_match:
                db.execute(
                    "UPDATE quote_body SET status = ?, sorder_num = ?  WHERE quote_num = ? AND line_ref = ? AND item_id = ? AND quantity = ? AND net_price = ? AND status = ? AND lead_time = ? LIMIT 1",
                    "SOLD", sorder_header[0]["order_num"], int(sorder_lines[i + 1]["quote_num"]), int(sorder_lines[i + 1]["line_ref"]), int(sorder_lines[i + 1]["item_id"]), 
                    int(sorder_lines[i + 1]["quantity"]), float(sorder_lines[i + 1]["net_price"]), "PENDING", 
                    int(sorder_lines[i + 1]["lead_time"])
                )
                continue
            # If there is not a perfect match, get a line with a bigger quantity. 
            # Update the first line and add a new line for pending quantity
            second_best = db.execute(
                "SELECT * FROM quote_body WHERE quote_num = ? AND line_ref = ? AND item_id = ? and quantity >= ? AND net_price = ? AND status = ? AND lead_time = ?",
                int(sorder_lines[i + 1]["quote_num"]), int(sorder_lines[i + 1]["line_ref"]), int(sorder_lines[i + 1]["item_id"]), int(sorder_lines[i + 1]["quantity"]),
                float(sorder_lines[i + 1]["net_price"]), "PENDING", int(sorder_lines[i + 1]["lead_time"])
            )
            if second_best:
                # Add a for loop to find the first line with enough quantity
                net_total_sold = round(int(sorder_lines[i + 1]["quantity"]) * float(sorder_lines[i + 1]["net_price"]), 2)
                db.execute(
                    "UPDATE quote_body SET status = ?, quantity = ?, line_net_total = ?, sorder_num = ? WHERE quote_num = ? AND line_ref = ? AND item_id = ? AND quantity >= ? AND net_price = ? AND status = ? AND lead_time = ? LIMIT 1",
                    "SOLD", int(sorder_lines[i + 1]["quantity"]), net_total_sold, int(sorder_header[0]["order_num"]), int(sorder_lines[i + 1]["quote_num"]), int(sorder_lines[i + 1]["line_ref"]), 
                    int(sorder_lines[i + 1]["item_id"]), int(sorder_lines[i + 1]["quantity"]), float(sorder_lines[i + 1]["net_price"]), "PENDING", int(sorder_lines[i + 1]["lead_time"])
                )
                remaining_quantity = second_best[0]["quantity"] - int(sorder_lines[i + 1]["quantity"])
                net_total_pending = round(remaining_quantity * second_best[0]["net_price"], 2)
                db.execute(
                    "INSERT INTO quote_body (quote_num, line_ref, item_id, item_desc, quantity, list_price, discount, net_price, line_net_total, lead_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    second_best[0]["quote_num"], second_best[0]["line_ref"], second_best[0]["item_id"], 
                    second_best[0]["item_desc"], remaining_quantity, second_best[0]["list_price"], second_best[0]["discount"],
                    second_best[0]["net_price"], net_total_pending, second_best[0]["lead_time"]
                )
                continue
            # Try a last search with no line_ref
            else:
                last_try = db.execute(
                    "SELECT * FROM quote_body WHERE quote_num = ? AND item_id = ? AND quantity >= ? AND net_price = ? AND status = ? AND lead_time = ?",
                    int(sorder_lines[i + 1]["quote_num"]), int(sorder_lines[i + 1]["item_id"]), 
                    int(sorder_lines[i + 1]["quantity"]), float(sorder_lines[i + 1]["net_price"]), 
                    "PENDING", int(sorder_lines[i + 1]["lead_time"])
                )
                if last_try:
                    db.execute(
                        "UPDATE quote_body SET status = ? WHERE quote_num = ? AND item_id = ? AND quantity >= ? AND net_price = ? AND status = ? AND sorder_num = ? AND lead_time = ? LIMIT 1",
                        "SOLD", sorder_lines[i + 1]["quote_num"], sorder_lines[i + 1]["line_ref"], sorder_lines[i + 1]["item_id"], 
                        int(sorder_lines[i + 1]["quantity"]), sorder_lines[i + 1]["net_price"], "PENDING", 
                        sorder_header[0]["order_num"], sorder_lines[i + 1]["lead_time"]
                    )
                    remaining_quantity = last_try[0]["quantity"] - int(sorder_lines[i + 1]["quantity"])
                    line_net_total = remaining_quantity * last_try[0]["net_price"]
                    db.execute(
                        "INSERT INTO quote_body (quote_num, line_ref, item_id, item_desc, quantity, list_price, discount, net_price, line_net_total, lead_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        last_try[0]["quote_num"], last_try[0]["line_ref"], last_try[0]["item_id"], 
                        last_try[0]["item_desc"], remaining_quantity, last_try[0]["list_price"], last_try[0]["discount"],
                        last_try[0]["net_price"], line_net_total, last_try[0]["lead_time"]
                    )
        # Update status of quote header
        # Make sure quote_body status only allows "PENDING", "SOLD", "LOST" values.
        statuses = db.execute(
            "SELECT DISTINCT status FROM quote_body WHERE quote_num = ?",
            sorder_lines[1]["quote_num"]
        )
        if len(statuses) == 1:
            if statuses[0]["status"] == "SOLD":
                db.execute(
                    "UPDATE quote_header SET status = ? WHERE quote_num = ?",
                    "SOLD", sorder_lines[1]["quote_num"]
                )
            elif statuses[0]["status"] == "LOST":
                db.execute(
                    "UPDATE quote_header SET status = ? WHERE quote_num = ?",
                    "LOST", sorder_lines[1]["quote_num"]
                )
        elif len(statuses) == 2:
            if statuses[0]["status"] != "PENDING" and statuses[1]["status"] != "PENDING":
                db.execute(
                    "UPDATE quote_header SET status = ? WHERE quote_num = ?",
                    "PARTIAL CLOSED", sorder_lines[1]["quote_num"]
                )
            else:
                db.execute(
                "UPDATE quote_header SET status = ? WHERE quote_num = ?",
                "PARTIAL OPEN", sorder_lines[1]["quote_num"]
            )
        else:
            db.execute(
                "UPDATE quote_header SET status = ? WHERE quote_num = ?",
                "PARTIAL OPEN", sorder_lines[1]["quote_num"]
            )

        # Unblock the quote to allow further modifications
        db.execute(
            "UPDATE quote_header SET blocked = ? WHERE quote_num = ?",
            int(0), request.form.get("quote_num")
        )

        # Send the user to the list of sorders
        return redirect("/get_all_sorders")



@app.route("/edit_sorder", methods=["GET", "POST"])
def edit_sorder():
    if request.method == "POST":

        # Get the data provided by user
        data = request.form.get("data")
        if not data:
            return render_template("error.html", message="There was an unexpected error. Contact your admin")
        sorder_lines = json.loads(data)


        # Check there is an sorder_header for this customer_id and status != DELIVERED
        sorder_header = db.execute(
            "SELECT * FROM sorder_header WHERE order_num = ? AND customer_id = ? AND status != ?",
            request.form.get("order_num"), request.form.get("customer_id"), "DELIVERED"
        )
        if not sorder_header:
            return render_template("error.html", message="Invalid action on sorder")
        #: Add new key/value to all the dictionaries in sorder_lines to compare and keep track
        #: of the lines checked against the quote_lines
        all_quotes_nos = []
        for i in range(len(sorder_lines)-1):
            sorder_lines[i+1]["checked"] = 0
            sorder_lines[i+1]["quote_num"] = int(sorder_lines[i+1]["quote_num"])
            sorder_lines[i+1]["net_price"] = float(sorder_lines[i+1]["net_price"])
            sorder_lines[i+1]["lead_time"] = int(sorder_lines[i+1]["lead_time"])
            sorder_lines[i+1]["item_id"] = int(sorder_lines[i+1]["item_id"])
            sorder_lines[i+1]["quantity"] = int(sorder_lines[i+1]["quantity"])

            all_quotes_nos.append(sorder_lines[i+1]["quote_num"])
        # Get the quote_nums as a list, but with only distinct quote numbers
        set_of_quotes_nos = set(all_quotes_nos)
        list_of_quote_numbers = list(set_of_quotes_nos)

        # Create a dict with all lines of the quotes involved in the current sorder
        for i in range(len(list_of_quote_numbers)):
            full_quote_lines = []
            customers_quote = db.execute(
                "SELECT * FROM quote_header WHERE quote_num = ? AND customer_id = ?",
                int(list_of_quote_numbers[i]), request.form.get("customer_id")
            )
            if not customers_quote:
                return render_template("error.html", message=f"Fatal error no quote no. {list_of_quote_numbers[i]}")
            full_quote_lines.extend(db.execute(
                "SELECT * FROM quote_body WHERE quote_num = ? AND status = ? AND sorder_num = ?",
                int(list_of_quote_numbers[i]), "SOLD", int(request.form.get("order_num"))
            ))
            full_quote_lines.extend(db.execute(
                "SELECT * FROM quote_body WHERE quote_num = ? AND status = ?",
                int(list_of_quote_numbers[i]), "PENDING"
            ))
        if not full_quote_lines:
            return render_template("error.html", message="No quote lines match your requirement")
        # Add a new key to the dict to use as a check list against the lines in the sorder
        for i in range(len(full_quote_lines)):
            full_quote_lines[i]["checked"] = 0

        #: Sort the full_quote_list by item_id and then by quantity, so when there is no match 
        #: with same qty, the 1st match will be the smallest one that fulfills all conditions
        full_quote_lines = sorted(full_quote_lines, key=itemgetter('quote_num', 'item_id', 'quantity'))

        # Iterate over every line in sorder_lines and find a match in full_quote_lines
        counter = 1
        for i in range(len(sorder_lines)-1):
            # Look for a match with exact quantity and status "sold"
            for j in range(len(full_quote_lines)):
                if full_quote_lines[j]["checked"] != 0 or int(sorder_lines[i+1]["quantity"]) != full_quote_lines[j]["quantity"]:
                    continue
                comp_keys = ["quote_num", "net_price", "lead_time", "item_id"]
                res = all(sorder_lines[i+1].get(key) == full_quote_lines[j].get(key) for key in comp_keys)
                if res is not True or full_quote_lines[j]["status"] != "SOLD":
                    continue
                # Why this is not working?
                full_quote_lines[j]["checked"] = counter
                sorder_lines[i+1]["checked"] = counter
                counter = counter + 1
                break
                # Look for a match with exact quantity and status "pending"
                for k in range(len(full_quote_lines)-1):
                    if full_quote_lines[k]["checked"] != 0 or sorder_lines[i+1]["quantity"] != full_quote_lines[k]["quantity"]:
                        continue
                    comp_keys = ["quote_num", "net_price", "lead_time", "item_id"]
                    res = all(sorder_lines[i+1].get(key) == full_quote_lines[k].get(key) for key in comp_keys)
                    if res is not True or full_quote_lines[k]["status"] != "PENDING":
                        continue    
                    full_quote_lines[k]["checked"] = counter
                    sorder_lines[i+1]["checked"] = counter
                    counter = counter + 1
                    break
                    # Look for a match with enough quantity and status "SOLD"
                    for l in range(len(full_quote_lines)-1):
                        if full_quote_lines[l]["checked"] != 0 or sorder_lines[i+1]["quantity"] > full_quote_lines[l]["quantity"]:
                            continue
                        comp_keys = ["quote_num", "net_price", "lead_time", "item_id"]
                        res = all(sorder_lines[i+1].get(key) == full_quote_lines[l].get(key) for key in comp_keys)
                        if res is not True or full_quote_lines[l]["status"] != "SOLD":
                            continue
                        # The first line that matches all conditions will be the smalest one available  
                        full_quote_lines[l]["checked"] = counter
                        sorder_lines[i+1]["checked"] = counter
                        counter = counter + 1
                        break
                        # if find a perfect match, break.
                        # else
                        for m in range(len(full_quote_lines)-1):
                            if full_quote_lines[m]["checked"] != 0 or sorder_lines[i+1]["quantity"] > full_quote_lines[m]["quantity"]:
                                if m < (len(full_quote_lines)-1):
                                    continue
                                else:
                                    return render_template ("error.html", message=f"Error on item {sorder_lines[i+1]['item_id']}")
                            comp_keys = ["quote_num", "net_price", "lead_time", "item_id"]
                            res = all(sorder_lines[i+1].get(key) == full_quote_lines[k].get(key) for key in comp_keys)
                            if res is not True or full_quote_lines[m]["status"] != "SOLD":
                                if m < (len(full_quote_lines)-1):
                                    continue
                                else:
                                    # If no match is found after a full iteration, return error.
                                    return render_template ("error.html", message=f"Error on item {sorder_lines[i+1]['item_id']}")
                            # The first line that matches all conditions will be the smalest one available  
                            full_quote_lines[m]["checked"] = counter
                            sorder_lines[i+1]["checked"] = counter
                            counter = counter + 1
                            break
        
        
        """      
        # Update the stock table by retrieving all item movs from old version of sorder
        sorder_mod_lines = db.execute(
            "SELECT * FROM sorder_body WHERE order_num = ? AND status != ?",
            int(request.form.get("order_num")), "DELIVERED"
        )
        for i in range(len(sorder_mod_lines)):
            stock = db.execute(
                "SELECT * FROM stock WHERE item_id = ?", sorder_mod_lines[i]["item_id"] 
            )
            # Increase available
            new_available = stock[0]["stock_available"] + sorder_mod_lines[i]["quantity"]
            # Decrease on sale
            new_onsale = stock[0]["stock_onsale"] - sorder_mod_lines[i]["quantity"]
            db.execute(
                "UPDATE stock SET stock_available = ?, stock_onsale = ? WHERE item_id = ?",
                new_available, new_onsale, sorder_mod_lines[i]["item_id"]
            )
        # Delete all previous sorder lines in status NOT "DELIVERED"
        db.execute(
            "DELETE FROM sorder_body WHERE order_num = ? AND status != ?",
            int(request.form.get("order_num")), "DELIVERED"
        )

        #: Upload to sorder_body all the lines included in the current version of sorder 
        #: (Except for the lines in DELIVERED status)
        for i in range(len(sorder_lines)- 1):
            if sorder_lines[i+1]["status"] == "DELIVERED":
                continue
            net_price = round((float(sorder_lines[i + 1]["list_price"]) * (1 - float(sorder_lines[i + 1]["discount"]))), 2)
            line_net_total = round((net_price * int(sorder_lines[i + 1]["quantity"])), 2)
            db.execute(
                "INSERT INTO sorder_body (order_num, line_ref, item_id, item_desc, quantity, list_price, discount, net_price, line_net_total, lead_time, delivery_date, po_number, quote_num) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                int(request.form.get("order_num")), int(sorder_lines[i + 1]["line_ref"]), int(sorder_lines[i + 1]["item_id"]),
                sorder_lines[i + 1]["description"], int(sorder_lines[i + 1]["quantity"]), float(sorder_lines[i + 1]["list_price"]), 
                float(sorder_lines[i + 1]["discount"]), net_price, line_net_total, int(sorder_lines[i + 1]["lead_time"]), 
                sorder_lines[i + 1]["delivery_date"], order_lines[i + 1]["po_num"], int(sorder_lines[i + 1]["quote_num"])
            )
            # Update stock table
            item_stocks = db.execute(
                "SELECT * FROM stock WHERE item_id = ?", int(sorder_lines[i + 1]["item_id"])
            )
            new_onsale = item_stocks[0]["stock_onsale"] + int(sorder_lines[i + 1]["quantity"])
            new_available = item_stocks[0]["stock_available"] - int(sorder_lines[i + 1]["quantity"])
            db.execute(
                "UPDATE stock SET stock_onsale = ?, stock_available = ? WHERE item_id = ?",
                new_onsale, new_available, int(sorder_lines[i + 1]["item_id"])
            )

        # Update sorder_header total_net_value
        full_net_total = db.execute(
            "SELECT SUM(line_net_total) FROM sorder_body WHERE order_num = ?",
            request.form.get("order_num")
        )
        db.execute(
            "UPDATE sorder_header SET total_net_value = ? WHERE order_num = ?",
            full_net_total[0]["SUM(line_net_total)"], request.form.get("order_num")
        )
        """
        
        # Update status of quote_body lines involved
        for i in range(len(sorder_lines)-1):
            filtered_list = [d for d in full_quote_lines if d['checked'] == sorder_lines[i+1]["checked"]]
            print("Filtered list: ")
            print(filtered_list)
            if sorder_lines[i+1]["quantity"] == filtered_list[0]["quantity"]:
                db.execute(
                    "UPDATE quote_body SET status = ?, sorder_num = ? WHERE quote_num = ? AND line_ref = ? AND item_id = ? AND quantity = ? AND net_price = ? AND lead_time = ? AND status = ? AND sorder_num = ?",
                    "SOLD", int(request.form.get("order_num")), filtered_list[0]["quote_num"], filtered_list[0]["line_ref"],
                    filtered_list[0]["item_id"], filtered_list[0]["quantity"], filtered_list[0]["net_price"],
                    filtered_list[0]["lead_time"], filtered_list[0]["status"], filtered_list[0]["sorder_num"]
                )
            else:
                remaining_qty =  filtered_list[0]["quantity"] - sorder_lines[i+1]["quantity"]
                db.execute(
                    "UPDATE quote_body SET status = ?, sorder_num = ? WHERE quote_num = ? AND line_ref = ? AND item_id = ? AND quantity = ? AND net_price = ? AND lead_time = ? AND status = ? AND sorder_num = ? LIMIT 1",
                    "SOLD", int(request.form.get("order_num")), filtered_list[0]["quote_num"], filtered_list[0]["line_ref"],
                    filtered_list[0]["item_id"], filtered_list[0]["quantity"], filtered_list[0]["net_price"],
                    filtered_list[0]["lead_time"], filtered_list[0]["status"], filtered_list[0]["sorder_num"]
                )
                db.execute(
                    "INSERT INTO quote_body (quote_num, line_ref, item_id, item_desc, quantity, list_price, discount, net_price, line_net_total, lead_time, sorder_num) VALUES (?, ?, ?, ?, ?, ?, ?, , ?, ?, ?, ?)",
                    filtered_list[0]["quote_num"], filtered_list[0]["line_ref"], filtered_list[0]["item_id"], 
                    remaining_qty, filtered_list[0]["net_price"], filtered_list[0]["lead_time"], 
                    filtered_list[0]["status"], filtered_list[0]["sorder_num"]
                )

        # Update those quote_body lines no longer used in this order. status to PENDING, sorder_num to NULL
        filtered_list = [d for d in full_quote_lines if d['checked'] == 0]
        if filtered_list:
            for i in range(len(filtered_list)):
                if filtered_list[i]["status"] == "SOLD" and filtered_list[i]["sorder_num"] == int(request.form.get("order_num")):
                    db.execute(
                        "UPDATE quote_body SET status = ?, order_num = ? WHERE WHERE quote_num = ? AND line_ref = ? AND item_id = ? AND quantity = ? AND net_price = ? AND lead_time = ? AND status = ? AND sorder_num = ? LIMIT 1",
                        "PENDING", "NULL", filtered_list[i]["quote_num"], filtered_list[i]["line_ref"],
                        filtered_list[i]["item_id"], filtered_list[i]["quantity"], filtered_list[i]["net_price"],
                        filtered_list[i]["lead_time"], filtered_list[i]["status"], filtered_list[i]["sorder_num"]
                    )
        
        """
        # Update status of quote header
        # Make sure quote_body status only allows "PENDING", "SOLD", "LOST" values.
        #FALTA CONSIDERAR LAS QUOTES QUE SE QUITARON POR COMPLETO DE LA PRESENTE SORDER

        for i in range(len(list_of_quote_numbers)):
            statuses = db.execute(
                "SELECT DISTINCT status FROM quote_body WHERE quote_num = ?",
                int(list_of_quote_numbers[i])
            )
            if len(statuses) == 1:
                if statuses[0]["status"] == "SOLD":
                    db.execute(
                        "UPDATE quote_header SET status = ? WHERE quote_num = ?",
                        "SOLD", int(list_of_quote_numbers[i])
                    )
                elif statuses[0]["status"] == "LOST":
                    db.execute(
                        "UPDATE quote_header SET status = ? WHERE quote_num = ?",
                        "LOST", int(list_of_quote_numbers[i])
                    )
                else:
                    db.execute(
                        "UPDATE quote_header SET status = ? WHERE quote_num = ?",
                        "PENDING", int(list_of_quote_numbers[i])
                    )
            elif len(statuses) == 2:
                if statuses[0]["status"] != "PENDING" and statuses[1]["status"] != "PENDING":
                    db.execute(
                        "UPDATE quote_header SET status = ? WHERE quote_num = ?",
                        "PARTIAL CLOSED", int(list_of_quote_numbers[i])
                    )
                else:
                    db.execute(
                    "UPDATE quote_header SET status = ? WHERE quote_num = ?",
                    "PARTIAL OPEN", int(list_of_quote_numbers[i])
                )
            else:
                db.execute(
                    "UPDATE quote_header SET status = ? WHERE quote_num = ?",
                    "PARTIAL OPEN", int(list_of_quote_numbers[i])
                )
    
        # Desbloquear todas las sorders y quotes (incluir solo involucradas en version final)
        db.execute("UPDATE quote_header SET blocked = ?", int(0))
        db.execute("UPDATE sorder_header SET blocked = ?", int(0))
        """

        # Send the user to the list of sorders
        return redirect("/get_all_sorders")
   
    
    if request.method == "GET":
        order_num = int(request.args.get("order_num"))
        if not order_num:
            return render_template("error.html", message="Error while getting the sorder. Contact your admin")
        header = db.execute(
            "SELECT * FROM sorder_header WHERE order_num = ? AND status != ?", 
            order_num, "DELIVERED"
        )
        if not header:
            return render_template("error.html", message="Forbidden action")
        # Check sorder is not already blocked by another instance
        if header[0]["blocked"] != 0:
            # If so, return the user to the detail of the sorder
            session["temp_sorder_num"] = int(order_num)
            return redirect("/sorder_details")

        # Check in sorder_body table every related quote num to make sure they arent either blocked
        sorder_quote_nums = db.execute(
            "SELECT DISTINCT quote_num FROM sorder_body WHERE order_num = ?", order_num
        )
        for i in range(len(sorder_quote_nums)):
            quote_header = db.execute(
                "SELECT * FROM quote_header WHERE quote_num = ?",
                sorder_quote_nums[i]["quote_num"]
            )
            if not quote_header:
                return render_template("error.html", message=f"Error: quote no. {sorder_quote_nums[i]['quote_num']}, related to this order is no longer active.")
            # Check quotes involved aren't blocked by another instance
            if quote_header[0]["blocked"] != 0:
                # If so, return the user to the detail of the sorder
                session["temp_sorder_num"] = int(order_num)
                return redirect("/sorder_details")
        
        # All been checked, proceed to block the sorder and all quotes involved
        db.execute(
            "UPDATE sorder_header SET blocked = ? WHERE order_num = ?",
            int(1), order_num
        )

        for i in range(len(sorder_quote_nums)):
            db.execute(
                "UPDATE quote_header SET blocked = ? WHERE quote_num = ?",
                int(1), sorder_quote_nums[i]["quote_num"]
            )
        # Get all lines from sorder_body
        bodies = db.execute (
            "SELECT * FROM sorder_body WHERE order_num = ?", order_num
        )

        # Hand the user the page with the full table to edit the sorder as required
        return render_template("edit_sorder.html", header=header, bodies=bodies)


# Get all sales orders
@app.route("/get_all_sorders", methods = ["GET"])
def get_all_sorders():
    sorders = db.execute("SELECT * FROM sorder_header ORDER BY order_num DESC")
    return render_template("sorders_list.html", sorders=sorders)


@app.route("/sorder_details", methods=["GET"])
def get_sorder_details():
    sorder_id = request.args.get("sorder_num")  
    if not sorder_id:
        header = db.execute("SELECT * FROM sorder_header WHERE order_num = ?", session["temp_sorder_num"])
        bodies = db.execute(
        "SELECT * FROM sorder_body WHERE order_num = ? ORDER BY line_ref", session["temp_sorder_num"]
        )
    else:
        header = db.execute("SELECT * FROM sorder_header WHERE order_num = ?", sorder_id)
        bodies = db.execute(
        "SELECT * FROM sorder_body WHERE order_num = ? ORDER BY line_ref", sorder_id
    )
    if not header:
        return render_template("error.html", message="Header could not be found!")
    length = len(bodies)
    if header[0]["blocked"] != 0:
        message = "This sales order is currently blocked by another user!!!"
        return render_template("sorder_details.html", length=length, header=header, bodies=bodies, message=message)
    return render_template("sorder_details.html", length=length, header=header, bodies=bodies)


@app.route("/get_sorder_by_id/<sorder_id>", methods = ["GET"])
def get_sorder_by_id(sorder_id):
    sorder_header = db.execute("SELECT * FROM sorder_header WHERE order_num = ?", sorder_id)
    sorder_body = db.execute ("SELECT * FROM sorder_body WHERE order_num = ?", sorder_id)
    return jsonify({"sorder_header": sorder_header}, {"sorder_body": sorder_body})


@app.route("/get_sorders_by_customer_id/<customer_id>", methods = ["GET"])
def get_sorders_by_customer_id(customer_id):
    # Get all the sorder_headers for this customer
    sorder_headers = db.execute("SELECT * FROM sorder_header WHERE customer_id = ?", customer_id)
    # Get me an empty list to store all the sorders as dictionaries
    sorders = []
    # For each sorder_num in header, get me all the body rows with that same sorder_num
    for i in range(len(sorder_headers)):
        sorder_body = db.execute("SELECT * FROM sorder_body WHERE order_num = ?", sorder_headers[i]["order_num"])
        sorders.append({"1_sorder_header": sorder_headers[i], "2_sorder_body": sorder_body})
    return jsonify(sorders)


# Pending implementation
@app.route("/get_sorders_by_status", methods = ["GET"])
def get_sorders_by_status():
    pass


# Pending implementation
@app.route("/get_sorders_by_customer_and_status", methods = ["GET"])
def get_sorders_by_customer_and_status():
    pass


@app.route("/positive_stock_adjustment", methods = ["POST"])
def positive_stock_adjustment():
    user_input = request.get_json()
    # Get current row of stock table for requested item
    item_stock = db.execute(
        "SELECT * FROM stock WHERE item_id = ?", 
        user_input["item_id"]
    )
    if not item_stock:
        return jsonify({"message": "invalid item"}), 400
    if not isinstance(user_input["quantity"], int) or user_input["quantity"] < 0:
        return jsonify({"message": "invalid quantity"}), 400
     # Get all stock columns involved in this adjustment and calculate new value
    updated_stock_total = item_stock[0]["stock_total"] + user_input["quantity"]
    updated_stock_appr = item_stock[0]["stock_approved"] + user_input["quantity"]
    updated_stock_available = item_stock[0]["stock_available"] + user_input["quantity"]

    # Update values in stock table
    db.execute(
        "UPDATE stock SET stock_total = ?, stock_approved = ?, stock_available = ? WHERE item_id = ?",
        updated_stock_total, updated_stock_appr, updated_stock_available, user_input["item_id"]
    )

    # Add movement to the table stock_moves
    db.execute(
        "INSERT INTO stock_moves (item_id, item_description, quantity, stock_bef, stock_aft, reference, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        item_stock[0]["item_id"], item_stock[0]["item_description"], user_input["quantity"], item_stock[0]["stock_total"], updated_stock_total, "positive_adjustment", user_input["user_id"] 
    )

    return jsonify({"message": "success"}), 200



@app.route("/negative_stock_adjustment", methods = ["POST"])
def negative_stock_adjustment():
    user_input = request.get_json()
    # Get current row of stock table for requested item
    item_stock = db.execute(
        "SELECT * FROM stock WHERE item_id = ?", 
        user_input["item_id"]
    )
    if not item_stock:
        return jsonify({"message": "invalid item"}), 400
    if not isinstance(user_input["quantity"], int) or user_input["quantity"] < 0:
        return jsonify({"message": "invalid quantity"}), 400
    # Get all stock columns involved in this adjustment and calculate new value
    updated_stock_total = item_stock[0]["stock_total"] - user_input["quantity"]
    updated_stock_appr = item_stock[0]["stock_approved"] - user_input["quantity"]
    updated_stock_available = item_stock[0]["stock_available"] - user_input["quantity"]

    # Update values in stock table
    db.execute(
        "UPDATE stock SET stock_total = ?, stock_approved = ?, stock_available = ? WHERE item_id = ?",
        updated_stock_total, updated_stock_appr, updated_stock_available, user_input["item_id"]
    )

    # Add movement to the table stock_moves
    db.execute(
        "INSERT INTO stock_moves (item_id, item_description, quantity, stock_bef, stock_aft, reference, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        item_stock[0]["item_id"], item_stock[0]["item_description"], user_input["quantity"], item_stock[0]["stock_total"], updated_stock_total, "negative_adjustment", user_input["user_id"] 
    )

    return jsonify({"message": "success"}), 200


@app.route("/list_of_deliveries", methods=["GET"])
def list_deliveries():
    deliveries = db.execute("SELECT * FROM delivery_header")
    return render_template("list_of_deliveries.html", deliveries=deliveries)

@app.route("/delivery_details", methods=["GET"])
def delivery_details():
    delivery_id = request.args.get("delivery_id")
    header = db.execute(
        "SELECT * FROM delivery_header WHERE id = ?", delivery_id
    )
    bodies = db.execute(
        "SELECT * FROM delivery_body WHERE id = ?", delivery_id
    )
    return render_template("delivery_details.html", header=header, bodies=bodies)


@app.route("/create_delivery", methods = ["POST"])
def create_delivery():
    user_input = request.get_json()
    # Check sorder_num and customer_id provided are a valid combination
    sorder_header = db.execute(
        "SELECT * FROM sorder_header WHERE order_num = ? AND customer_id = ? AND status != ?",
        user_input["sorder_num"], user_input["customer_id"], "DELIVERED"
    )
    if not sorder_header:
        return jsonify({"message": "invalid customer_id/sorder_num combination"})
    # Get all the pending lines from sorder_body
    sorder_body = db.execute(
        "SELECT * FROM sorder_body WHERE order_num = ? AND status = ?",
        user_input["sorder_num"], "PENDING"
    )
    if not sorder_body:
        return jsonify({"message": "this order has no pending items"}), 400
    # Check there is enough stock of all the items the user wants to deliver
    # If the loop makes it to the end without breaking, I can start creating the delivery
    for i in range(len(sorder_body)):
        item_stock = db.execute(
            "SELECT * FROM stock WHERE item_id = ?", sorder_body[i]["item_id"]
        )
        if item_stock[0]["stock_approved"] < sorder_body[i]["quantity"]:
            return jsonify({"message": "stock insufficient", "item": sorder_body[i]["item_id"]})
    # If customer indicates delivery address as "default" must bring the info from user table.
    if user_input["delivery_address"].upper() == "DEFAULT":
        customer_info = db.execute(
            "SELECT * FROM customers WHERE id = ?", user_input["customer_id"]
        )
        delivery_address = customer_info[0]["address_street"] + ", " + customer_info[0]["address_city"] + "."
    # If user provides a different address, this one will be used.
    else:
        delivery_address = user_input["delivery_address"]
    # Create the delivery_header
    db.execute(
        "INSERT INTO delivery_header (customer_id, delivery_address, created_by) VALUES (?, ?, ?)",
        user_input["customer_id"], delivery_address, user_input["created_by"]
    )

    # Get the delivery header just created to use the id
    delivery_header = db.execute("SELECT * FROM delivery_header ORDER BY id DESC LIMIT 1")
    
    # Keep track of the total net value to update it in the body_header
    total_net_value = 0
    # Complete the delivery_body with all rows
    for i in range(len(sorder_body)):
        total_net_value = total_net_value + sorder_body[i]["net_price"] * sorder_body[i]["quantity"]
        db.execute(
            "INSERT INTO delivery_body (id, item_id, line_ref, quantity, sorder_num, net_price) VALUES (?, ?, ?, ?, ?, ?)",
            delivery_header[0]["id"], sorder_body[i]["item_id"], sorder_body[i]["line_ref"], sorder_body[i]["quantity"],
            sorder_body[i]["order_num"], sorder_body[i]["net_price"]
        )
        # Update sorder_body status for every line to "ON DELIVERY"
        db.execute(
            "UPDATE sorder_body SET status = ? WHERE item_id = ? AND line_ref = ? AND order_num = ?",
            "ON DELIVERY", sorder_body[i]["item_id"], sorder_body[i]["line_ref"], sorder_body[i]["order_num"] 
        )
    # Update delivery_header total_net_value
    db.execute(
        "UPDATE delivery_header SET total_net_value = ? WHERE id = ?",
        total_net_value, delivery_header[0]["id"]
    )

    return jsonify({"message": "delivery receipt created", "delivery_id": delivery_header[0]["id"]})


@app.route("/validate_delivery", methods = ["POST"])
def validate_delivery():
    user_input = request.get_json()
    # Check there is a delivery that matches user_input and is pending validation.
    delivery_header = db.execute(
        "SELECT * FROM delivery_header WHERE id = ? AND customer_id = ? AND status = ?",
        user_input["delivery_id"], user_input["customer_id"], "CREATED" 
    )
    if not delivery_header:
        return jsonify({"message": "invalid customer_id/delivery combination or already validated"})
    # Change delivery_header status to "validated"
    db.execute(
        "UPDATE delivery_header SET status = ? WHERE id = ?",
        "VALIDATED", user_input["delivery_id"]
    )
    # Get all lines from delivery_body current id
    delivery_body = db.execute(
        "SELECT * FROM delivery_body WHERE id = ?", user_input["delivery_id"]
    )
    # Update stock status for all items of the current delivery_body
    stock_move_reference = "DELIVERY ID " + str(user_input["delivery_id"])
    for i in range(len(delivery_body)):
        current_item_stock = db.execute(
            "SELECT * FROM stock WHERE item_id = ?", 
            delivery_body[i]["item_id"]
        )
        updated_stock_total = current_item_stock[0]["stock_total"] - delivery_body[i]["quantity"]
        updated_stock_approved = current_item_stock[0]["stock_approved"] - delivery_body[i]["quantity"]
        updated_stock_onsale = current_item_stock[0]["stock_onsale"] - delivery_body[i]["quantity"]
        db.execute(
            "UPDATE stock SET stock_total = ?, stock_approved = ?, stock_onsale = ? WHERE item_id = ?",
            updated_stock_total, updated_stock_approved, updated_stock_onsale, delivery_body[i]["item_id"]
        )
        # Includes this operation in table stock_moves for each item line
        db.execute(
            "INSERT INTO stock_moves (item_id, item_description, quantity, stock_bef, stock_aft, reference, customer_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            delivery_body[i]["item_id"], "NO DESCRIPTION", delivery_body[i]["quantity"], current_item_stock[0]["stock_total"], updated_stock_total,
            stock_move_reference, user_input["customer_id"], user_input["created_by"]
        )

    return jsonify({"message": "delivery validation ok"})


@app.route("/current_stock", methods=["GET"])
def get_current_stock():
    stocks = db.execute("SELECT * FROM stock")
    return render_template("current_stock.html", stocks=stocks)

@app.route("/stock_movement", methods=["GET"])
def get_stock_movements():
    moves = db.execute("SELECT * FROM stock_moves")
    return render_template("stock_movements.html", moves=moves)


@app.route("/get_all_invoices", methods=["GET"])
def get_all_invoices():
    invoices = db.execute("SELECT * FROM invoice_header")
    return render_template("invoices.html", invoices=invoices)

@app.route("/invoice_details", methods=["GET"])
def get_invoice_details():
    invoice_num = request.args.get("invoice_num")
    header = db.execute(
        "SELECT * FROM invoice_header WHERE invoice_num = ?", invoice_num
    )
    bodies = db.execute(
        "SELECT * FROM invoice_body WHERE invoice_num = ?", invoice_num
    )
    return render_template("invoice_details.html", header=header, bodies=bodies)



@app.route("/create_invoice_from_delivery", methods = ["POST"])
def create_invoice_from_delivery():
    user_input = request.get_json()
    # Check there is a validated delivery that matches user_input
    delivery_header = db.execute(
        "SELECT * FROM delivery_header WHERE id = ? AND customer_id = ? AND status = ?",
        user_input["delivery_id"], user_input["customer_id"], "VALIDATED"
    )
    if not delivery_header:
        return jsonify({"message": "invalid delivery_id/customer or delivery not available"}), 400
    # Get all the item lines from that delivery
    delivery_body = db.execute(
        "SELECT * FROM delivery_body WHERE id = ?", user_input["delivery_id"]
    )
    # Create invoice_header // for now only handles cash payment
    total_tax_amount = delivery_header[0]["total_net_value"] * tax_rate
    db.execute(
        "INSERT INTO invoice_header (customer_id, total_net_value, total_tax_amount, status, created_by) VALUES (?, ?, ?, ?, ?)",
        delivery_header[0]["customer_id"], delivery_header[0]["total_net_value"], total_tax_amount, "CREATED", user_input["created_by"]
    )
    # Get the invoice_header to use the invoice_id in the body lines
    invoice_header = db.execute("SELECT * FROM invoice_header ORDER BY invoice_num DESC LIMIT 1")

    # Create the invoice_body for all the items
    for i in range(len(delivery_body)):
        tax_amount = delivery_body[i]["net_price"] * tax_rate
        db.execute(
            "INSERT INTO invoice_body (invoice_num, line_ref, sorder_num, delivery_id, item_id, quantity, net_price, tax_amount) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            invoice_header[0]["invoice_num"], delivery_body[i]["line_ref"], delivery_body[i]["sorder_num"],
            user_input["delivery_id"], delivery_body[i]["item_id"], delivery_body[i]["quantity"], 
            delivery_body[i]["net_price"], tax_amount
        )
    # Update delivery_header change status and include invoice_num
    db.execute(
        "UPDATE delivery_header SET status = ?, invoice_num = ? WHERE ID = ?",
        "INVOICED", invoice_header[0]["invoice_num"], delivery_header[0]["id"]
    )
    # Confirm operation success
    return jsonify({"message": "invoice created ok", "invoice_num": invoice_header[0]["invoice_num"]})
    

if __name__ == "__main__":
        app.run(debug=True)


