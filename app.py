from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# =====================
# DATABASE MODELS
# =====================

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to expenses
    expenses = db.relationship('Expense', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'


class Expense(db.Model):
    """Expense model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Expense {self.category} - ${self.amount}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =====================
# ROUTES
# =====================

@app.route('/')
def index():
    """Home page - redirect to dashboard if logged in"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required!', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard - show stats and summary"""
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    
    # Calculate totals
    total_expenses = sum(e.amount for e in expenses)
    
    # Category breakdown
    category_totals = {}
    for expense in expenses:
        if expense.category in category_totals:
            category_totals[expense.category] += expense.amount
        else:
            category_totals[expense.category] = expense.amount
    
    # Recent expenses (last 5)
    recent_expenses = sorted(expenses, key=lambda x: x.date, reverse=True)[:5]
    
    return render_template('dashboard.html', 
                         total_expenses=total_expenses,
                         category_totals=category_totals,
                         recent_expenses=recent_expenses,
                         username=current_user.username)


@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    """Add new expense"""
    if request.method == 'POST':
        amount = request.form.get('amount')
        category = request.form.get('category')
        description = request.form.get('description')
        date = request.form.get('date')
        
        # Validation
        if not amount or not category or not date:
            flash('Please fill all required fields!', 'error')
            return redirect(url_for('add_expense'))
        
        try:
            amount = float(amount)
            date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid amount or date!', 'error')
            return redirect(url_for('add_expense'))
        
        # Create expense
        new_expense = Expense(
            user_id=current_user.id,
            amount=amount,
            category=category,
            description=description or 'No description',
            date=date
        )
        
        db.session.add(new_expense)
        db.session.commit()
        
        flash('Expense added successfully!', 'success')
        return redirect(url_for('view_expenses'))
    
    return render_template('add_expense.html')


@app.route('/expenses')
@login_required
def view_expenses():
    """View all expenses"""
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    
    # Sort by date (newest first)
    expenses = sorted(expenses, key=lambda x: x.date, reverse=True)
    
    total = sum(e.amount for e in expenses)
    
    return render_template('view_expenses.html', expenses=expenses, total=total)


@app.route('/delete_expense/<int:expense_id>')
@login_required
def delete_expense(expense_id):
    """Delete an expense"""
    expense = Expense.query.get(expense_id)
    
    # Security check - user can only delete their own expenses
    if expense and expense.user_id == current_user.id:
        db.session.delete(expense)
        db.session.commit()
        flash('Expense deleted successfully!', 'success')
    else:
        flash('You cannot delete this expense!', 'error')
    
    return redirect(url_for('view_expenses'))


@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out!', 'success')
    return redirect(url_for('login'))


# =====================
# ERROR HANDLERS
# =====================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500


# =====================
# RUN APP
# =====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)