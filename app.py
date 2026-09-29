import os
from datetime import datetime
from decimal import Decimal
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-change-this-secret")
database_url = os.getenv("DATABASE_URL", "sqlite:///finance.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    incomes = db.relationship("Income", backref="user", lazy=True, cascade="all, delete-orphan")
    expenses = db.relationship("Expense", backref="user", lazy=True, cascade="all, delete-orphan")

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(12,2), nullable=False)
    source = db.Column(db.String(120), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # YYYY-MM
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(12,2), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    note = db.Column(db.String(255))
    spent_on = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def current_month():
    return datetime.now().strftime("%Y-%m")

def advisor_insights(income, expenses):
    total = sum((Decimal(str(e.amount)) for e in expenses), Decimal("0"))
    remaining = Decimal(str(income)) - total
    by_category = {}
    for e in expenses:
        by_category[e.category] = by_category.get(e.category, Decimal("0")) + Decimal(str(e.amount))

    tips = []
    if income <= 0:
        tips.append("Add your monthly income to generate a personalized budget.")
    elif total > income:
        tips.append("Your recorded expenses are above income. Review non-essential spending first.")
    else:
        savings_rate = (remaining / Decimal(str(income))) * 100
        if savings_rate < 10:
            tips.append("Try to build toward saving at least 10% of monthly income.")
        elif savings_rate < 20:
            tips.append("Your savings are positive. Consider gradually increasing the savings rate toward 20%.")
        else:
            tips.append("Your current recorded savings rate is strong. Consider assigning part of it to a specific goal.")

    if by_category:
        largest = max(by_category, key=by_category.get)
        tips.append(f"Highest spending category: {largest} (₹{by_category[largest]:,.2f}).")
        if income > 0 and by_category[largest] > Decimal(str(income)) * Decimal("0.30"):
            tips.append(f"{largest} is above 30% of income; consider setting a lower monthly limit.")

    tips.append("Use the category breakdown each week to catch overspending early.")
    return tips, by_category, total, remaining

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("landing.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 6:
            flash("Enter your name, a valid email, and a password of at least 6 characters.", "error")
            return render_template("register.html")
        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists. Please log in.", "error")
            return redirect(url_for("login"))
        user = User(name=name, email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Incorrect email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    month = request.args.get("month", current_month())
    incomes = Income.query.filter_by(user_id=current_user.id, month=month).all()
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.spent_on.desc()).all()
    monthly_income = sum((Decimal(str(i.amount)) for i in incomes), Decimal("0"))
    monthly_expenses = [e for e in expenses if e.spent_on.strftime("%Y-%m") == month]
    tips, by_category, total, remaining = advisor_insights(monthly_income, monthly_expenses)
    return render_template(
        "dashboard.html",
        month=month,
        incomes=incomes,
        expenses=monthly_expenses,
        income=monthly_income,
        total=total,
        remaining=remaining,
        by_category=by_category,
        tips=tips,
    )

@app.route("/income", methods=["POST"])
@login_required
def add_income():
    amount = request.form.get("amount", "0")
    source = request.form.get("source", "").strip()
    month = request.form.get("month", current_month())
    try:
        value = Decimal(amount)
        if value <= 0 or not source:
            raise ValueError
    except Exception:
        flash("Enter a valid income amount and source.", "error")
        return redirect(url_for("dashboard"))
    db.session.add(Income(amount=value, source=source, month=month, user_id=current_user.id))
    db.session.commit()
    flash("Income added.", "success")
    return redirect(url_for("dashboard", month=month))

@app.route("/expense", methods=["POST"])
@login_required
def add_expense():
    try:
        amount = Decimal(request.form.get("amount", "0"))
        category = request.form.get("category", "").strip()
        note = request.form.get("note", "").strip()
        spent_on = datetime.strptime(request.form.get("spent_on"), "%Y-%m-%d").date()
        if amount <= 0 or not category:
            raise ValueError
    except Exception:
        flash("Enter valid expense details.", "error")
        return redirect(url_for("dashboard"))
    db.session.add(Expense(amount=amount, category=category, note=note, spent_on=spent_on, user_id=current_user.id))
    db.session.commit()
    return redirect(url_for("dashboard", month=spent_on.strftime("%Y-%m")))

@app.route("/api/summary")
@login_required
def api_summary():
    month = request.args.get("month", current_month())
    incomes = Income.query.filter_by(user_id=current_user.id, month=month).all()
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    expenses = [e for e in expenses if e.spent_on.strftime("%Y-%m") == month]
    income = sum((Decimal(str(i.amount)) for i in incomes), Decimal("0"))
    tips, categories, total, remaining = advisor_insights(income, expenses)
    return jsonify({
        "month": month,
        "income": float(income),
        "expenses": float(total),
        "savings": float(remaining),
        "categories": {k: float(v) for k, v in categories.items()},
        "tips": tips
    })

@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database initialized.")

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
