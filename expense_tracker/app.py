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
    date = db.Column(db.Date, nullable = False)
    created_at = db.Column(db.DateTime, default = datetime.utcnow)
    
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
        #get form data
        amount = request.form.get('amount')
        category = request.form.get('category')
        description = request.form.get('description')
        date_str = request.form.get('date')
        
        #validate data
        if not amount or not category or not date_str:
            flash('Please fill in all required fields!', 'error')
            return redirect(url_for('add_expense'))
        
        try:
            amount = float(amount)
            #convert date string to date object
            date=datetime.strptime(date_str, '%Y-%m-%d').date()
            
            new_expense = Expense(
                amount = amount,
                category = category,
                description = description,
                date = date
            )
            
            #add to database
            db.session.add(new_expense)
            db.session.commit()
            
            flash('Expense added successfully!', 'success')
            return redirect(url_for(index))
        
        except ValueError:
            flash('Invalid amount or data format!', 'error')
            return redirect(url_for('add_expense'))
    #GET request - show the form
    return render_template('add_expense.html')

@app.route('/delete/<int:expense_id>')
def delete_expense(expense_id):
    #delete an expense
    expense = Expense.query.get_or_404(expense_id)
    
    try:
        db.session.delete(expense)
        db.session.commit()
        flash('Expense delete successfully!', 'success')
    except:
        flash('Error deleting expense!', 'error')
        
    return redirect(url_for('index'))

#run app
if __name__ == '__main__':
    app.run(debug=True)