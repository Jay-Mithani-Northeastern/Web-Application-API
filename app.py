from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from util.db import Users,Products, db
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
    return {"message": "Endpoint is healthy"},200
 
 
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
    user = Users.query.filter_by(username=username).first()
    db.session.commit()
    schema = {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "account_created": user.account_created,
        "account_updated": user.account_updated
    } 
    return schema,201


@app.route('/v1/user/<userId>', methods =['GET'])
def get_user_details(userId):
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        return {"message":message},401
    username_from_user, password_from_user = Encryption.decode(header)
    user = Users.query.filter_by(username=username_from_user).first()

    
    if user is None:
        return {"message":"Invalid Credentials"},401
    elif not Encryption.isValidPassword(password_from_user,user.password):
        return {"message": "Invalid Credentials"},401
    elif user.id!=int(userId):
        return {"message":"Forbidden"},403
    schema = {
        "id": userId,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "account_created": user.account_created,
        "account_updated": user.account_updated
    }
    return schema,200

@app.route('/v1/user/<userId>', methods =['PUT'])
def update_user_details(userId):
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        return {"message":message},401
    username_from_user, password_from_user = Encryption.decode(header)
    user = Users.query.filter_by(username=username_from_user).first()

    if user is None:
        return {"message":"Invalid Credentials"},401
    elif not Encryption.isValidPassword(password_from_user,user.password):
        return {"message": "Invalid Credentials"},401
    elif user.id!=int(userId):
        return {"message":"Forbidden"},403

    mandatory = ["first_name","last_name","username"]
    data = request.get_json()
    if any(k not in data.keys() for k in mandatory):
        return {"message": "Mandatory fields : first_name, last_name, username, password"},400
    elif any(k not in ("first_name","last_name","password","username") for k in data.keys()):
        return {"message":"Updated restricted to first_name, last_name, password only"},400
    elif data.get("username") is None:
        return {"message":"Please enter username"},400
    elif data.get("first_name") == "" or data.get("last_name") == "" or data.get("password") == "" or data.get("username")=="":
        return {"message":"Fields cannot be empty"},400
    elif username_from_user!=data.get("username"):
        return {"message":"Please enter correct username in username field"}
        
    
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
    user = Users.query.filter_by(username=username_from_user).first()

    if user is None:
        return {"message":"Invalid Credentials"},401
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

    is_SameSKU_available = Products.query.filter_by(sku=sku).first()
    if is_SameSKU_available:
        return {"message":"Product with same SKU already exist"},400
    
    new_product = Products(name=name, description=description, sku=sku, manufacturer=manufacturer,quantity=quantity,owner_user_id=owner_user_id)
    db.session.add(new_product)
    db.session.commit()
    product = Products.query.filter_by(sku=sku).first()
    schema = {
        "id" : product.id,
        "name" : product.name,
        "description" : product.description,
        "sku" : product.sku,
        "manufacturer" : product.manufacturer,
        "quantity" : product.quantity,
        "date_added" : product.date_added,
        "date_last_updated" :product.date_last_updated,
        "owner_user_id" : product.owner_user_id
    }
    return schema,201


@app.route('/v1/product/<productId>', methods =['GET'])
def get_product_details(productId):
    product = Products.query.get(productId)
    if not product:
        return {"message":"Product Not Found"},404
    schema = {
        "id" : product.id,
        "name" : product.name,
        "description" : product.description,
        "sku" : product.sku,
        "manufacturer" : product.manufacturer,
        "quantity" : product.quantity,
        "date_added" : product.date_added,
        "date_last_updated" :product.date_last_updated,
        "owner_user_id" : product.owner_user_id
    }
    return schema,200

@app.route('/v1/product/<productId>', methods =['PUT'])
def update_product_details(productId):
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        return {"message":message},401
    username_from_user, password_from_user = Encryption.decode(header)
    
    user = Users.query.filter_by(username=username_from_user).first()
    if user is None:
        return {"message":"Invalid Credentials"},401
    elif not Encryption.isValidPassword(password_from_user,user.password):
        return {"message": "Invalid Credentials"},401

    product = Products.query.filter_by(id=productId).first()
    if product is None or product.owner_user_id!=user.id:
        return {"message":"Forbidden"},403
    

    data = request.get_json()
    message = Validation.isProductDataValid(data)
    if message!="":
        return {"message":message},400
    
    name = data.get("name")
    description =  data.get("description")
    sku =  data.get("sku")
    manufacturer = data.get("manufacturer")
    quantity = data.get("quantity")
    is_updated = False
    if sku is not None:
        is_product_already_present = Products.query.filter_by(sku=sku).first()
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
        is_updated = True
        product.quantity = int(quantity)
    if is_updated:
        product.date_last_updated = datetime.now()
        db.session.commit()

    return {},204

@app.route('/v1/product/<productId>', methods =['PATCH'])
def replace_product_details(productId):
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        return {"message":message},401
    username_from_user, password_from_user = Encryption.decode(header)
    
    user = Users.query.filter_by(username=username_from_user).first()
    if user is None:
        return {"message":"Invalid Credentials"},401
    elif not Encryption.isValidPassword(password_from_user,user.password):
        return {"message": "Invalid Credentials"},401

    product = Products.query.filter_by(id=productId).first()
    if product is None or product.owner_user_id!=user.id:
        return {"message":"Forbidden"},403

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
        if  not isinstance("test",type(sku)):
            return {"message":"Invalid datatype : name, description, sku, manufacturer can only contain characters"},400
        else:
            is_product_already_present = Products.query.filter_by(sku=sku).first()
            if is_product_already_present:
                return {"message":"Product with same sku already exist"},400
            else:
                is_updated = True
                product.sku = sku
    if name is not None:
        if  not isinstance("test",type(name)):
            return {"message":"Invalid datatype : name, description, sku, manufacturer can only contain characters"},400
        else:
            is_updated = True
            product.name = name 
    if description is not None:
        if  not isinstance("test",type(description)):
            return {"message":"Invalid datatype : name, description, sku, manufacturer can only contain characters"},400
        else:
            is_updated = True
            product.description = description
    if manufacturer is not None:
        if  not isinstance("test",type(manufacturer)):
            return {"message":"Invalid datatype : name, description, sku, manufacturer can only contain characters"},400
        else:
            is_updated = True
            product.manufacturer = manufacturer
    if quantity is not None:
        temp_int=1
        temp_float=1.0
        print(type(temp_int),type(quantity))
        if type(temp_float)==type(quantity):
            if abs(int(quantity)-quantity)!=0:
                return {"message" : "Quantity cannot contain floating values"},400
        elif type(temp_int)!=type(quantity):
            return {"message" : "Quantity should be an integer"},400
        elif quantity<0:
            return {"message" : "Quantity cannot be negative"},400
        else:
            is_updated = True
            product.quantity = int(quantity)
    if is_updated:
        product.date_last_updated = datetime.now()
        db.session.commit()

    return {},204

@app.route('/v1/product/<productId>', methods =['DELETE'])
def delete_product(productId):
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        return {"message":message},401
    username_from_user, password_from_user = Encryption.decode(header)
    user = Users.query.filter_by(username=username_from_user).first()
    if user is None:
        return {"message":"Invalid Credentials"},401
    elif not Encryption.isValidPassword(password_from_user,user.password):
        return {"message": "Invalid Credentials"},401

    product = Products.query.filter_by(id=productId).first()
    if product is None or product.owner_user_id!=user.id:
        return {"message":"Forbidden"},403
    
    db.session.delete(product)
    db.session.commit()
    return {},204


if __name__ == '__main__':
    app.run()