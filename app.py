from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from util.db import Users,Product, db
from util.validations import Validation
from util.encrypt import Encryption
from datetime import datetime
import os
from dotenv import load_dotenv
import re

load_dotenv()
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config['JSON_SORT_KEYS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/healthz', methods =['GET'])
def health():
    return {"message": "Endpoint is healthy"}
 
 
@app.route('/v1/user', methods = ['POST'])
def create_user():
    data = request.get_json()
    message = Validation.isUserDataValid(data)
    if message != "":
        return {"message" : message},400
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    username = data.get('username')
    password = data.get('password')

    user = Users.query.filter_by(username=username).first()
    if user:
        return {"message":"User already exist"},400

    password = Encryption.encrypt(password)
    new_user = Users(first_name=first_name, last_name=last_name, username=username, password=password)
    db.session.add(new_user)
    user_id = Users.query.filter_by(username=username).first().id
    account_created = Users.query.filter_by(username=username).first().account_created
    account_updated = Users.query.filter_by(username=username).first().account_updated

    db.session.commit()
    schema = {
        "id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "account_created": account_created,
        "account_updated": account_updated
    } 
    return schema,201


@app.route('/v1/product/<productId>', methods =['GET'])
def get_product_details(productId):
    product = Product.query.get(productId)
    if not product:
        return {"message":"Product Not Found"},404
    schema = {
        "id" : Product.query.filter_by(id=productId).first().id,
        "name" : Product.query.filter_by(id=productId).first().name,
        "description" : Product.query.filter_by(id=productId).first().description,
        "sku" : Product.query.filter_by(id=productId).first().sku,
        "manufacturer" : Product.query.filter_by(id=productId).first().manufacturer,
        "quantity" : Product.query.filter_by(id=productId).first().quantity,
        "date_added" : Product.query.filter_by(id=productId).first().date_added,
        "date_last_updated" : Product.query.filter_by(id=productId).first().date_last_updated,
        "owner_user_id" : Product.query.filter_by(id=productId).first().owner_user_id
    }
    return schema,200

# Authenticated End-Points
@app.route('/v1/user/<userId>', methods =['GET'])
def get_user_details(userId):
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        return {"message":message},401


    username_from_user, password_from_user = Encryption.decode(header)
    print(username_from_user,password_from_user)
    user = Users.query.filter_by(username=username_from_user).first()

    
    if user is None:
        return {"message":"Forbidden"},403
    elif not Encryption.isValidPassword(password_from_user,user.password):
        return {"message": "Invalid Credentials"},401
    elif user.username == username_from_user and Encryption.isValidPassword(password_from_user,user.password) and user.id != int(userId):
        return {"message": "Forbidden"},403
    schema = {
        "id": userId,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "account_created": user.account_created,
        "account_updated": user.account_updated
    } 
    db.session.commit()
    return schema,200

@app.route('/v1/user/<userId>', methods =['PUT'])
def update_user_details(userId):
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        return {"message":message},401
    username_from_user, password_from_user = Encryption.decode(header)
    print(username_from_user,password_from_user)
    user = Users.query.filter_by(username=username_from_user).first()

    if user is None:
        return {"message":"Forbidden"},403
    elif not Encryption.isValidPassword(password_from_user,user.password):
        return {"message": "Invalid Credentials"},401
    elif user.username == username_from_user and Encryption.isValidPassword(password_from_user,user.password) and user.id != int(userId):
        return {"message": "Forbidden"},403

    data = request.get_json()
    if any(k not in ("first_name","last_name","password") for k in data.keys()):
        return {"message":"Updated restricted to first_name, last_name, password only"},400
    if data.get("first_name") == "" or data.get("last_name") == "" or data.get("password") == "":
        return {"message":"Fields cannot be empty"},400
        
    
    isUpdated = False
    if data.get("first_name") is not None:
        isUpdated = True
        user.first_name = data.get("first_name")
    if data.get("last_name") is not None:
        isUpdated = True
        user.last_name = data.get("last_name")
    if data.get("password") is not None:
        isUpdated = True
        user.password = Encryption.encrypt(data.get("password"))
    if isUpdated:
        user.account_updated = datetime.now()
        db.session.commit()
    return {},204


@app.route('/v1/product', methods =['POST'])
def add_product():
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        return {"message":message},401
    username_from_user, password_from_user = Encryption.decode(header)
    print(username_from_user,password_from_user)
    user = Users.query.filter_by(username=username_from_user).first()

    if user is None:
        return {"message":"Forbidden"},403
    elif not Encryption.isValidPassword(password_from_user,user.password):
        return {"message": "Invalid Credentials"},401
    
    data = request.get_json()
    message = Validation.isProductDataValid(data)
    if message!="":
        return {"message":message},400
    
    
    name = data.get("name")
    description = data.get("description")
    sku = data.get("sku")
    manufacturer = data.get("manufacturer")
    quantity = int(data.get("quantity"))
    owner_user_id = Users.query.filter_by(username=username_from_user).first().id

    is_SameSKU_available = Product.query.filter_by(sku=sku).first()
    if is_SameSKU_available:
        return {"message":"Product with same SKU already exist"},400
    
    new_product = Product(name=name, description=description, sku=sku, manufacturer=manufacturer,quantity=quantity,owner_user_id=owner_user_id)
    db.session.add(new_product)
    db.session.commit()
    return {"message": "Product Added"},201


@app.route('/v1/product/<productId>', methods =['PUT'])
def update_product_details(productId):
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        return {"message":message},401
    username_from_user, password_from_user = Encryption.decode(header)
    print(username_from_user,password_from_user)
    product = Product.query.filter_by(id=productId).first()

    if product is None:
        return {"message":"Forbidden"},403
    
    user = Users.query.filter_by(id=product.owner_user_id).first()
    
    if not Encryption.isValidPassword(password_from_user,user.password) or user.username != username_from_user:
        return {"message": "Invalid Credentials"},401
    # elif user.username == username_from_user and Encryption.isValidPassword(password_from_user,user.password) and user.id != int(userId):
    #     return {"message": "Forbidden"},403

    data = request.get_json()
    if any(k not in ("name","description","sku", "manufacturer", "quantity") for k in data.keys()):
        return {"message":"Updated restricted to name, description, sku, manufacturer, quantity only"},400
    if data.get("name") == "" or data.get("description") == "" or data.get("sku") == "" or data.get("manufacturer") == "" or data.get("quantity") == "":
        return {"message":"Fields cannot be empty"},400
    
    name = data.get("name")
    description =  data.get("description")
    sku =  data.get("sku")
    manufacturer = data.get("manufacturer")
    quantity = data.get("quantity")
    is_updated = False
    if sku is not None:
        is_product_already_present = Product.query.filter_by(sku=sku).first()
        if is_product_already_present:
            return {"message":"Product with same sku already exist"},400
        else:
            is_updated = True
            product.sku = sku
    if name is not None:
        is_updated = True
        product.name = name 
    if description is not None:
        is_updated = True
        product.description = description
    if manufacturer is not None:
        is_updated = True
        product.manufacturer = manufacturer
    if quantity is not None:
        if not(re.match(r'^\d+$',quantity)) or int(quantity)<1:
            return {"message" : "Quantity should be an integer > 0"},400
        else:
            product.quantity = quantity
    if is_updated:
        product.date_last_updated = datetime.now()
        db.session.commit()

    return {},204

# @app.route('/v1/product/<productId>', methods =['PATCH'])
# def update_product_details():
#     return {"message": "Endpoint is healthy"}

@app.route('/v1/product/<productId>', methods =['DELETE'])
def delete_product(productId):
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        return {"message":message},401
    username_from_user, password_from_user = Encryption.decode(header)
    print(username_from_user,password_from_user)
    product = Product.query.filter_by(id=productId).first()

    if product is None:
        return {"message":"Product Not Found"},404
    
    user = Users.query.filter_by(id=product.owner_user_id).first()
    
    if not Encryption.isValidPassword(password_from_user,user.password) or user.username != username_from_user:
        return {"message": "Invalid Credentials"},401
    db.session.delete(product)
    db.session.commit()
    return {},204


if __name__ == '__main__':
    app.run()