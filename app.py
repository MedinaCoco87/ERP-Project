import os

from cs50 import SQL
from flask import Flask, jsonify, redirect, request
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from auxiliary import login_required


# Configuring flask app
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure database
db = SQL("sqlite:///erpdatabase.db")

# Configure Session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
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


# Pending vinculation with frontend
@app.route("/customers/<customer_id>", methods = ["GET"])
def get_customer_by_id(customer_id):
    customer = db.execute("SELECT * FROM customers WHERE id = ?", customer_id)
    if not customer:
        return jsonify({"message": "customer not found"}), 400
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



# Pending vinculation to frontend
@app.route ("/items/<item_id>", methods = ["GET"])
def get_item_by_id(item_id):
    item = db.execute("SELECT * FROM items WHERE id = ?", item_id)
    if not item:
        return jsonify({"messagge": "item not found"}), 400
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
    quotes = db.execute("SELECT * FROM quote_header")
    return render_template("quotes_list.html", quotes=quotes)
    # Get me an empty list to store all the quotes as dictionaries
    #quotes = []
    # For each quote_num in header, get me all the body rows with that same quote_num
    #for i in range(len(quote_headers)):
        #quote_body = db.execute("SELECT * FROM quote_body WHERE quote_num = ?", quote_headers[i]["quote_num"])
        #quotes.append({"1_quote_header": quote_headers[i], "2_quote_body": quote_body})
    #return jsonify(quotes)


@app.route ("/create_quote", methods = ["POST"])
def create_quote():
    # Get the full json data
    full_quote = request.get_json()
    # Separate header from body
    quote_header = full_quote["quote_header"]
    quote_body = full_quote["quote_body"]
    # Update first headers table to generate the quote number
    db.execute ("INSERT INTO quote_header (customer_id, created_by) VALUES (?, ?)", quote_header["customer_id"], quote_header["created_by"])
    # Get the quote number to use it in quote body
    last_header = db.execute("SELECT * FROM quote_header ORDER BY quote_num DESC LIMIT 1")
    quote_number = last_header[0]["quote_num"]
    # Loop through all lines of quote body and insert into quote body table
    for i in range(len(quote_body)):
        line_net_total = quote_body[i]["list_price"] * (1 - quote_body[i]["discounts"]) *  quote_body[i]["quantity"]
        db.execute(
            "INSERT INTO quote_body (quote_num, line_ref, item_id, quantity, list_price, discounts, line_net_total, lead_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
            quote_number, quote_body[i]["line_ref"], quote_body[i]["item_id"], quote_body[i]["quantity"], 
            quote_body[i]["list_price"], quote_body[i]["discounts"], line_net_total, quote_body[i]["lead_time"]
        )
    # Get the full total from body to update headers table
    full_net_total = db.execute(
        "SELECT SUM(line_net_total) FROM quote_body WHERE quote_num = ?", quote_number,
    )
    db.execute(
        "UPDATE quote_header SET total_net_value = ? WHERE quote_num = ?",
        full_net_total[0]["SUM(line_net_total)"], quote_number
    )
    return jsonify({"message": "quote created"})



@app.route("/get_quote_by_id/<quote_id>", methods = ["GET"])
def get_quote_by_id(quote_id):
    quote_header = db.execute("SELECT * FROM quote_header WHERE quote_num = ?", quote_id)
    quote_body = db.execute ("SELECT * FROM quote_body WHERE quote_num = ?", quote_id)
    full_quote = jsonify({"quote_header": quote_header}, {"quote_body": quote_body})
    return full_quote




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



@app.route("/convert_quote_to_sorder", methods = ["POST"])
def convert_quote_to_sorder():
    sorder_input = request.get_json()

    # Check there is a quote_header row that matches both customer_id and quote_num
    quote_header = db.execute(
        "SELECT * FROM quote_header WHERE quote_num = ? AND customer_id = ?",
        sorder_input["quote_num"], sorder_input["customer_id"])

    if not quote_header:
        return jsonify({"message": "invalid quote_num customer_id combination"}), 400
    
    # Get ALL the item lines from quote_body with status "PENDING"
    quote_body = db.execute(
        "SELECT * FROM quote_body WHERE quote_num = ? AND status = ?", 
        sorder_input["quote_num"], "PENDING"
    )

    # Making sure the quote has some pending items to be converted
    if not quote_body:
        return jsonify({"message": "this quote is no longer available"}), 400

    # Create the sorder_header to generate the order_num
    db.execute(
        "INSERT INTO sorder_header (customer_id, created_by) VALUES (?, ?)",
        sorder_input["customer_id"], sorder_input["created_by"]
    )
    
    # Get the sorder_header just created to use its order_num
    sorder_header = db.execute(
        "SELECT * FROM sorder_header ORDER BY order_num DESC LIMIT 1"
    )

    # Insert converted items as rows in sorder_body.
    # Keep track of total_net_value to update it in sorder_header
    total_net_value = 0
    for i in range(len(quote_body)):
        net_price = quote_body[i]["list_price"] * (1 - quote_body[i]["discounts"])
        total_net_value = total_net_value + (net_price * quote_body[i]["quantity"])
        db.execute(
            "INSERT INTO sorder_body (order_num, line_ref, item_id, quantity, net_price, delivery_date, quote_num) VALUES (?, ?, ?, ?, ?, ?, ?)",
            sorder_header[0]["order_num"], quote_body[i]["line_ref"], quote_body[i]["item_id"], quote_body[i]["quantity"], net_price, 
            sorder_input["delivery_date"], quote_body[i]["quote_num"]
        )
        # Get the current row of stock for the item
        stock_row = db.execute( 
            "SELECT * FROM stock WHERE item_id = ?", quote_body[i]["item_id"]
        )
        # Calculate the new stock values for the columns affected
        new_stock_onsale = stock_row[0]["stock_onsale"] + quote_body[i]["quantity"]
        new_stock_available = stock_row[0]["stock_available"] - quote_body[i]["quantity"]
        # Update item values in stock table (+stock_onsale, -stock_available)
        db.execute(
            "UPDATE stock SET stock_onsale = ?, stock_available = ? WHERE item_id = ?",
            new_stock_onsale, new_stock_available, quote_body[i]["item_id"]
        )

    # Update sorder_header with the total_net_value
    db.execute(
        "UPDATE sorder_header SET total_net_value = ? WHERE order_num = ?",
        total_net_value, sorder_header[0]["order_num"]
    )

    # Update status of quote_body items to "sold"
    db.execute(
        "UPDATE quote_body SET status = ? WHERE quote_num = ?",
        "SOLD", sorder_input["quote_num"]
    )

    # Return success message
    return jsonify({"message": "sales_order created", "order_num": sorder_header[0]["order_num"]}
    )


@app.route("/partial_quote_to_sorder", methods = ["POST"])
def partial_quote_to_sorder():
    user_input = request.get_json()
    # Check the quote_num and customer_id provided are a valid combination
    quote_header = db.execute(
        "SELECT * FROM quote_header WHERE quote_num = ? AND customer_id = ?",
        user_input["quote_num"], user_input["customer_id"]
    )
    if not quote_header:
        return jsonify({"message": "invalid customer_id quote_num combination"})
    
    # Check items provided by user are valid for sale
    items = user_input["items"]
    quote_body = []
    for i in range(len(items)):
        quote_body_row = db.execute(
            "SELECT * FROM quote_body WHERE quote_num = ? AND item_id = ? AND line_ref = ? AND status = ?",
              user_input["quote_num"], items[i]["item_id"], items[i]["line_ref"], "PENDING" 
        )
        if not quote_body_row:
            return jsonify({"message": "invalid item", "reference": items[i]["item_id"]}), 400
        quote_body.append(quote_body_row[0])

    # Create the sorder_header to generate the order_num
    db.execute(
        "INSERT INTO sorder_header (customer_id, created_by) VALUES (?, ?)",
        user_input["customer_id"], user_input["created_by"]
    )

    # Get the sorder_header just created to use its order_num
    sorder_header = db.execute(
        "SELECT * FROM sorder_header ORDER BY order_num DESC LIMIT 1"
    )

    # Keep track of total_net_value to update it in sorder_header
    total_net_value = 0
    # Iterate over all the available rows in the quote 
    for i in range(len(quote_body)):
        # Calculate net price and update total_net_value through all the iteration
        net_price = quote_body[i]["list_price"] * (1 - quote_body[i]["discounts"])
        total_net_value = total_net_value + (net_price * quote_body[i]["quantity"])
        # Insert all requested items as rows in sorder_body.
        db.execute(
            "INSERT INTO sorder_body (order_num, line_ref, item_id, quantity, net_price, delivery_date, quote_num) VALUES (?, ?, ?, ?, ?, ?, ?)",
            sorder_header[0]["order_num"], quote_body[i]["line_ref"], quote_body[i]["item_id"], quote_body[i]["quantity"], net_price, 
            user_input["delivery_date"], quote_body[i]["quote_num"]
        )
        # Change status of every item in quote_body to sold
        db.execute(
            "UPDATE quote_body SET status = ? WHERE quote_num = ? AND item_id = ? AND line_ref = ?",
            "SOLD", quote_body[i]["quote_num"], quote_body[i]["item_id"], quote_body[i]["line_ref"]
        )
        # Get the current status of stock for the item
        stock_row = db.execute( 
            "SELECT * FROM stock WHERE item_id = ?", quote_body[i]["item_id"]
        )
        # Calculate the new stock values for the columns affected
        new_stock_onsale = stock_row[0]["stock_onsale"] + quote_body[i]["quantity"]
        new_stock_available = stock_row[0]["stock_available"] - quote_body[i]["quantity"]
        # Update item values in stock table (+ stock_onsale, - stock_available)
        db.execute(
            "UPDATE stock SET stock_onsale = ?, stock_available = ? WHERE item_id = ?",
            new_stock_onsale, new_stock_available, quote_body[i]["item_id"]
        )

    # Update sorder_header with the total_net_value
    db.execute(
        "UPDATE sorder_header SET total_net_value = ? WHERE order_num = ?",
        total_net_value, sorder_header[0]["order_num"]
    )
     
    # Return success message
    return jsonify({"message": "sales order succesfully created", "order_num": sorder_header[0]["order_num"]})
    


# Get all sales orders
@app.route("/get_all_sorders", methods = ["GET"])
def get_all_sorders():
    sorder_headers = db.execute("SELECT * FROM sorder_header")
    # Get me an empty list to store all the sorderss as dictionaries
    sorders = []
    # For each order_num in header, get all the sorder_body rows with that same order_num
    for i in range(len(sorder_headers)):
        sorder_body = db.execute("SELECT * FROM sorder_body WHERE order_num = ?", sorder_headers[i]["order_num"])
        sorders.append({"1_sorder_header": sorder_headers[i], "2_sorder_body": sorder_body})
    return jsonify(sorders)


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


