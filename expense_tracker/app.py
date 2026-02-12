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