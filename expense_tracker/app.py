from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import func, extract
import csv
from io import StringIO

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Database Model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Expense {self.category}: ${self.amount}>'

# Create database tables
with app.app_context():
    db.create_all()

# Helper function to get date range presets
def get_date_range(filter_type):
    """Returns start and end dates based on filter type"""
    today = datetime.now().date()
    
    if filter_type == 'today':
        return today, today
    elif filter_type == 'week':
        start = today - timedelta(days=today.weekday())
        return start, today
    elif filter_type == 'month':
        start = today.replace(day=1)
        return start, today
    elif filter_type == 'year':
        start = today.replace(month=1, day=1)
        return start, today
    
    return None, None

# Routes
@app.route('/')
def index():
    # home page to displays all expenses
    # Get filter parameters
    category_filter = request.args.get('category', '')
    date_filter = request.args.get('date_filter', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Start with base query
    query = Expense.query
    
    # Apply category filter
    if category_filter:
        query = query.filter_by(category=category_filter)
    
    # Apply date filter
    if date_filter:
        start, end = get_date_range(date_filter)
        if start and end:
            query = query.filter(Expense.date >= start, Expense.date <= end)
    elif start_date and end_date:
        # Custom date range
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Expense.date >= start, Expense.date <= end)
        except ValueError:
            flash('Invalid date format!', 'error')
    
    # Get filtered expenses
    expenses = query.order_by(Expense.date.desc()).all()
    
    # Calculate total
    total = sum(expense.amount for expense in expenses)
    
    # Get all unique categories for filter dropdown
    categories = db.session.query(Expense.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('index.html', 
                         expenses=expenses, 
                         total=total,
                         categories=categories,
                         current_category=category_filter,
                         current_date_filter=date_filter)

@app.route ('/add', methods = ['GET', 'POST'])
def add_expense():
    #for adding new expenses
    if request.method == 'POST':
        amount = request.form.get('amount')
        category = request.form.get('category')
        description = request.form.get('description')
        date_str = request.form.get('date')
        
        if not amount or not category or not date_str:
            flash('Please fill in all required fields!', 'error')
            return redirect(url_for('add_expense'))
        
        try:
            amount = float(amount)
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            new_expense = Expense(
                amount = amount,
                category = category,
                description = description,
                date = date
            )
            
            db.session.add(new_expense)
            db.session.commit()
            
            flash('Expense added successfully!', 'success')
            return redirect(url_for('index'))
            
        except ValueError:
            flash('Invalid amount or date format!', 'error')
            return redirect(url_for('add_expense'))
    
    return render_template('add_expense.html')

@app.route('/edit/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    """Edit an existing expense"""
    expense = Expense.query.get_or_404(expense_id)
    
    if request.method == 'POST':
        amount = request.form.get('amount')
        category = request.form.get('category')
        description = request.form.get('description')
        date_str = request.form.get('date')
        
        if not amount or not category or not date_str:
            flash('Please fill in all required fields!', 'error')
            return redirect(url_for('edit_expense', expense_id=expense_id))
        
        try:
            expense.amount = float(amount)
            expense.category = category
            expense.description = description
            expense.date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            db.session.commit()
            
            flash('Expense updated successfully!', 'success')
            return redirect(url_for('index'))
            
        except ValueError:
            flash('Invalid amount or date format!', 'error')
            return redirect(url_for('edit_expense', expense_id=expense_id))
    
    return render_template('edit_expense.html', expense=expense)

@app.route('/delete/<int:expense_id>')
def delete_expense(expense_id):
    #delete an expense
    expense = Expense.query.get_or_404(expense_id)
    
    try:
        db.session.delete(expense)
        db.session.commit()
        flash('Expense deleted successfully!', 'success')
    except:
        flash('Error deleting expense!', 'error')
    
    return redirect(url_for('index'))

@app.route('/statistics')
def statistics():
    """Show detailed statistics"""
    # Category-wise spending
    category_stats = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total'),
        func.count(Expense.id).label('count')
    ).group_by(Expense.category).all()
    
    # Monthly spending (last 6 months)
    six_months_ago = datetime.now().date() - timedelta(days=180)
    monthly_stats = db.session.query(
        extract('year', Expense.date).label('year'),
        extract('month', Expense.date).label('month'),
        func.sum(Expense.amount).label('total')
    ).filter(Expense.date >= six_months_ago)\
     .group_by('year', 'month')\
     .order_by('year', 'month').all()
    
    # Format monthly stats for Chart.js
    months = []
    amounts = []
    for stat in monthly_stats:
        month_name = datetime(int(stat.year), int(stat.month), 1).strftime('%b %Y')
        months.append(month_name)
        amounts.append(float(stat.total))
    
    # Total statistics
    total_expenses = Expense.query.count()
    total_spent = db.session.query(func.sum(Expense.amount)).scalar() or 0
    avg_expense = total_spent / total_expenses if total_expenses > 0 else 0
    
    return render_template('statistics.html',
                         category_stats=category_stats,
                         months=months,
                         amounts=amounts,
                         total_expenses=total_expenses,
                         total_spent=total_spent,
                         avg_expense=avg_expense)

@app.route('/export')
def export_csv():
    """Export all expenses to CSV"""
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    
    # Create CSV in memory
    si = StringIO()
    writer = csv.writer(si)
    
    # Write header
    writer.writerow(['Date', 'Category', 'Description', 'Amount'])
    
    # Write data
    for expense in expenses:
        writer.writerow([
            expense.date.strftime('%Y-%m-%d'),
            expense.category,
            expense.description or '',
            f'{expense.amount:.2f}'
        ])
    
    # Create response
    output = si.getvalue()
    si.close()
    
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=expenses.csv'}
    )

# Run the app
if __name__ == '__main__':
    app.run(debug=True)