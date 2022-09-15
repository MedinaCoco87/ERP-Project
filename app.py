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



@app.route ("/category_by_id/<item_category>", methods = ["GET"])
def get_category(item_category):
    category = db.execute("SELECT * FROM item_categories WHERE id = ?", item_category)
    return jsonify(category), 200



@app.route ("/get_all_categories", methods = ["GET"])
def get_all_categories():
    categories = db.execute("SELECT * FROM item_categories")
    if not categories:
        return jsonify({"message": "there are no records in categories yet"}), 400
    return jsonify(categories), 200



@app.route ("/items", methods = ["POST"])
def create_item():
    # Get json from postman
    item = request.get_json()
    # Identify the category for the new item and get the category full row from its table.
    item_category_row = db.execute("SELECT * FROM item_categories WHERE id = ?", item["category_id"])
    if not item_category_row:
        return jsonify({"message": "invalid category"}), 400
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




@app.route ("/items/<item_id>", methods = ["GET"])
def get_item_by_id(item_id):
    item = db.execute("SELECT * FROM items WHERE id = ?", item_id)
    if not item:
        return jsonify({"messagge": "item not found"}), 400
    return jsonify(item), 200




@app.route ("/items_by_category/<category_id>", methods = ["GET"])
def get_items_by_category(category_id):
    items = db.execute("SELECT * FROM items WHERE category_id = ?", category_id)
    if not items:
        return jsonify({"message": "this category is empty"}), 400
    return jsonify(items), 200




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




@app.route("/get_all_quotes", methods = ["GET"])
def get_all_quotes():
    quote_headers = db.execute("SELECT * FROM quote_header")
    # Get me an empty list to store all the quotes as dictionaries
    quotes = []
    # For each quote_num in header, get me all the body rows with that same quote_num
    for i in range(len(quote_headers)):
        quote_body = db.execute("SELECT * FROM quote_body WHERE quote_num = ?", quote_headers[i]["quote_num"])
        quotes.append({"1_quote_header": quote_headers[i], "2_quote_body": quote_body})
    return jsonify(quotes)




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

    # Making sure the quote has any pending items to be converted
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

    # Insert only requested items as rows in sorder_body.
    # Keep track of total_net_value to update it in sorder_header
    total_net_value = 0
    for i in range(len(quote_body)):
        net_price = quote_body[i]["list_price"] * (1 - quote_body[i]["discounts"])
        total_net_value = total_net_value + (net_price * quote_body[i]["quantity"])
        db.execute(
            "INSERT INTO sorder_body (order_num, line_ref, item_id, quantity, net_price, delivery_date, quote_num) VALUES (?, ?, ?, ?, ?, ?, ?)",
            sorder_header[0]["order_num"], quote_body[i]["line_ref"], quote_body[i]["item_id"], quote_body[i]["quantity"], net_price, 
            user_input["delivery_date"], quote_body[i]["quote_num"]
        )
    
    # Update sorder_header with the total_net_value
    db.execute(
        "UPDATE sorder_header SET total_net_value = ? WHERE order_num = ?",
        total_net_value, sorder_header[0]["order_num"]
    )
    
    # Change status of every item in quote_body to sold
    for i in range(len(quote_body)):
        db.execute(
            "UPDATE quote_body SET status = ? WHERE quote_num = ? AND item_id = ? AND line_ref = ?",
            "SOLD", quote_body[i]["quote_num"], quote_body[i]["item_id"], quote_body[i]["line_ref"]
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
    full_sorder = jsonify({"sorder_header": sorder_header}, {"sorder_body": sorder_body})
    return full_sorder


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




if __name__ == "__main__":
        app.run(debug=True)


