from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    account_created = db.Column(db.DateTime, nullable=False, default=datetime.now())
    account_updated = db.Column(db.DateTime, nullable=False, default=datetime.now())

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(100), unique =True, nullable=False)
    manufacturer = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.now())
    date_last_updated = db.Column(db.DateTime, nullable=False, default=datetime.now())
    owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

