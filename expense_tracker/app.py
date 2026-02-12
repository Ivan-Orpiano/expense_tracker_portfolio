from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime 

#Initialize flask
app = Flask(__name__)

#for configuration
app.config[''] = 'secret key in production' # FOR FLASH MESSAGES
app.config[''] = 'sqlite:///expenses.db' # SQLITE DATABASE
app.config['SQLALCHEMY'] = False

#initialize database
db = SQLAlchemy(app)

#Database model for expenses table

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    amount = db.Column(db.Float, nullable = False)
    category = db.Column(db.String(50), nullable = False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, default = datetime.utcnow)
    
    def __repr__(self):
        return f'<Expense {self.category}: ${self.amount}>'
    
with app.app_context():
    db.create_all
    
@app.route('/')
def index():
    # home page to displays all expenses
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    
    total = sum(expense.amount for expense in expenses)
    
    return render_template('expense_index.html', expenses=expenses, total=total)

@app.route ('/add', methods = ['GET', 'POST'])
def add_expense():
    #for adding new expenses
    if request.method == 'POST':
        pass