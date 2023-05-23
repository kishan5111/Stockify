import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
# Update the configuration
app.config['SESSION_COOKIE_NAME'] = 'your_session_cookie_name'
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")
os.environ['API_KEY'] = "your_api_key"

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Get user ID from session
    user_id = session.get("user_id")
    username = db.execute("SELECT username FROM users WHERE id = ?", user_id)[0]

    # Get current cash balance
    current_cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]['cash']

    # Get stock data for the user
    stock_owned = db.execute("SELECT symbol, stock_name, SUM(shares) AS total_shares, SUM(total_price) AS total FROM stock_purchases WHERE user_id = ? GROUP BY stock_name", user_id)

    if stock_owned:
        # Get current prices of stocks
        current_prices = []
        for stock in stock_owned:
            symbol = stock['symbol']
            stock_info = lookup(symbol)
            current_price = stock_info['price']
            current_prices.append(current_price)

        # Calculate total values of stocks
        total_values = []
        for stock, current_price in zip(stock_owned, current_prices):
            total = stock['total_shares'] * current_price
            total_values.append(total)

        current_cash = float(current_cash)  # Convert current_cash to a float

        # Calculate the grand total by summing up the total values of stocks and the current cash balance
        grand_total = sum(total_values) + current_cash

        # Zip stock_owned, current_prices, and total_values together
        stock_data = zip(stock_owned, current_prices, total_values)

        return render_template("homepage.html", username=username, current_cash=current_cash, stock_data=stock_data, grand_total=grand_total)
    else:
        return render_template("homepage.html", username=username, stock_data=None, current_cash=0, grand_total=0)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        shares = int(request.form.get("shares"))

        if not symbol or not shares:
            return apology("Please provide symbol and shares", 403)
        if shares <= 0:
            return apology("Shares cannot be 0 or negative", 403)

        stock = lookup(symbol)
        if stock is None:
            return apology("Invalid symbol", 403)
        price = float(stock['price'])
        total_price = price * shares

        # Get user ID from session
        user_id = session.get("user_id")

        # Get current cash balance of the user
        current_cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]['cash']

        # Check if the user has enough cash to make the purchase
        if total_price > current_cash:
            return apology("Not enough cash", 403)

        # Update cash balance
        updated_cash = current_cash - total_price
        db.execute("UPDATE users SET cash = ? WHERE id = ?", updated_cash, user_id)

        # Record the purchase in the stock_purchases table
        db.execute("INSERT INTO stock_purchases (user_id, symbol, stock_name, shares, price, total_price, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   user_id, symbol, stock['name'], shares, price, total_price, datetime.now())

        flash("Stock purchased successfully!")

        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # Get user ID from session
    user_id = session.get("user_id")

    # Get transaction history of the user
    transactions = db.execute(
        "SELECT symbol, stock_name, shares, price, total_price, timestamp FROM stock_purchases WHERE user_id = ? ORDER BY timestamp DESC", user_id)

    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return apology("Please provide username and password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("Invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol").upper()

        if not symbol:
            return apology("Please provide a symbol", 403)

        stock = lookup(symbol)
        if stock is None:
            return apology("Invalid symbol", 403)

        return render_template("quoted.html", stock=stock)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username or not password or not confirmation:
            return apology("Please provide username, password, and confirmation", 403)
        if password != confirmation:
            return apology("Passwords must match", 403)

        # Check if username already exists
        existing_user = db.execute("SELECT * FROM users WHERE username = ?", username)
        if existing_user:
            return apology("Username already exists", 403)

        # Insert new user into the database
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, generate_password_hash(password))

        # Log in the new user automatically
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        session["user_id"] = rows[0]["id"]

        flash("Registered successfully!")

        return redirect("/")

    else:
        return render_template("register.html")
