from flask import Flask, request, redirect
from flask_sqlalchemy import SQLAlchemy
from util.db import Users, Products, ProductImage, db
from util.validations import Validation
from util.encrypt import Encryption
from datetime import datetime
from util.s3 import s3, upload_file_to_s3, delete_object_from_s3
import os
from dotenv import load_dotenv
import uuid
import imghdr 
import logging
import statsd

load_dotenv()
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config['JSON_SORT_KEYS'] = False
app.config['S3_BUCKET'] = os.environ.get("S3_BUCKET_NAME")
db.init_app(app)


with app.app_context():
    db.create_all()

format = '%(message)s'
logging.basicConfig(filename='./logs/app.log', level=logging.DEBUG, format=format)
c = statsd.StatsClient('localhost', 8125)

@app.route('/healthz', methods =['GET'])
def health():
    c.incr('Healthz')
    logging.info("INFO:"+'Healthz API started')
    logging.info("INFO:"+'Healthz API ended')
    return {"message": "Endpoint is healthy"},200
 
 
@app.route('/v1/user', methods = ['POST'])
def create_user():
    c.incr('Create_User')
    logging.info("INFO:"+'Create User API started')
    data = request.get_json()
    message = Validation.isUserDataValid(data)
    if message != "":
        logging.error("Error:"+message)
        return {"message" : message},400
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    username = data.get('username')
    password = data.get('password')

    user = Users.query.filter_by(username=username).first()
    if user:
        logging.error("Error:"+'User already exist')
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
    logging.info("INFO:"+'Create User API ended')
    return schema,201


@app.route('/v1/user/<userId>', methods =['GET'])
def get_user_details(userId):
    c.incr('Get_User')
    logging.info("INFO:"+'Get User Details API started')
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        logging.error("Error:"+message)
        return {"message":message},401
    username_from_user, password_from_user = Encryption.decode(header)
    user = Users.query.filter_by(username=username_from_user).first()
    uId = Users.query.filter_by(id=userId).first()
    if user is None:
        logging.error("Error:"+'Invalid Credentials')
        return {"message":"Invalid Credentials"},401
    elif not Encryption.isValidPassword(password_from_user,user.password):
        logging.error("Error:"+'Invalid Credentials')
        return {"message": "Invalid Credentials"},401
    elif user.id!=int(userId) and uId is not None:
        logging.error("Error:"+'Forbidden')
        return {"message":"Forbidden"},403
    elif uId is None:
        logging.error("Error:"+'User ID Not Found')
        return {"message":"User ID Not Found"},404
    schema = {
        "id": userId,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "account_created": user.account_created,
        "account_updated": user.account_updated
    }
    logging.info("INFO:"+'Get User Details API started')
    return schema,200

@app.route('/v1/user/<userId>', methods =['PUT'])
def update_user_details(userId):
    c.incr('Update_User')
    logging.info("INFO:"+'Update User API started')
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        logging.error("Error:"+message)
        return {"message":message},401
    username_from_user, password_from_user = Encryption.decode(header)
    user = Users.query.filter_by(username=username_from_user).first()
    uId = Users.query.filter_by(id=userId).first()
    if user is None:
        logging.error("Error:"+'Invalid Credentials')
        return {"message":"Invalid Credentials"},401
    elif not Encryption.isValidPassword(password_from_user,user.password):
        logging.error("Error:"+'Invalid Credentials')
        return {"message": "Invalid Credentials"},401
    elif user.id!=int(userId) and uId is not None:
        logging.error("Error:"+'Forbidden')
        return {"message":"Forbidden"},403
    elif uId is None:
        logging.error("Error:"+'User ID Not Found')
        return {"message":"User ID Not Found"},404

    mandatory = ["first_name","last_name","username"]
    data = request.get_json()
    if any(k not in data.keys() for k in mandatory):
        logging.error("Error:"+'Mandatory fields : first_name, last_name, username, password')
        return {"message": "Mandatory fields : first_name, last_name, username, password"},400
    elif any(k not in ("first_name","last_name","password","username") for k in data.keys()):
        logging.error("Error:"+'Updated restricted to first_name, last_name, password only')
        return {"message":"Updated restricted to first_name, last_name, password only"},400
    elif data.get("username") is None:
        logging.error("Error:"+'Please enter username')
        return {"message":"Please enter username"},400
    elif data.get("first_name") == "" or data.get("last_name") == "" or data.get("password") == "" or data.get("username")=="":
        logging.error("Error:"+'Fields cannot be empty')
        return {"message":"Fields cannot be empty"},400
    elif username_from_user!=data.get("username"):
        logging.error("Error:"+'Please enter correct username in username field')
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
    logging.info("INFO:"+'Update User API ended')
    return {},204


@app.route('/v1/product', methods =['POST'])
def add_product():
    c.incr('Create_Product')
    logging.info("INFO:"+'Create Product API started')
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        logging.error("Error:"+message)
        return {"message":message},401
    username_from_user, password_from_user = Encryption.decode(header)
    user = Users.query.filter_by(username=username_from_user).first()

    if user is None:
        logging.error("Error:"+'Invalid Credentials')
        return {"message":"Invalid Credentials"},401
    elif not Encryption.isValidPassword(password_from_user,user.password):
        logging.error("Error:"+'Invalid Credentials')
        return {"message": "Invalid Credentials"},401
  
    data = request.get_json()
    message = Validation.isProductDataValid(data)
    if message!="":
        logging.error("Error:"+message)
        return {"message":message},400
    
    
    name = data.get("name")
    description = data.get("description")
    sku = data.get("sku")
    manufacturer = data.get("manufacturer")
    quantity = int(data.get("quantity"))
    owner_user_id = Users.query.filter_by(username=username_from_user).first().id

    is_SameSKU_available = Products.query.filter_by(sku=sku).first()
    if is_SameSKU_available:
        logging.error("Error:"+'Product with same SKU already exist')
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
    logging.info("INFO:"+'Create Product API ended')
    return schema,201


@app.route('/v1/product/<productId>', methods =['GET'])
def get_product_details(productId):
    c.incr('Get_Product')
    logging.info("INFO:"+'Get Product API started')
    product = Products.query.get(productId)
    if not product:
        logging.error("Error:"+'Product Not Found')
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
    logging.info("INFO:"+'Get Product API ended')
    return schema,200

@app.route('/v1/product/<productId>', methods =['PUT'])
def update_product_details(productId):
    c.incr('Update_Product')
    logging.info("INFO:"+'Update Product API started')
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        logging.error("Error:"+message)
        return {"message":message},401
    username_from_user, password_from_user = Encryption.decode(header)
    
    user = Users.query.filter_by(username=username_from_user).first()
    if user is None:
        logging.error("Error:"+'Invalid Credentials')
        return {"message":"Invalid Credentials"},401
    elif not Encryption.isValidPassword(password_from_user,user.password):
        logging.error("Error:"+'Invalid Credentials')
        return {"message": "Invalid Credentials"},401

    product = Products.query.filter_by(id=productId).first()
    if product is not None and product.owner_user_id!=user.id:
        logging.error("Error:"+'Forbidden')
        return {"message":"Forbidden"},403
    elif product is None:
        logging.error("Error:"+'Product Not Found')
        return {"message":"Product Not Found"},404
    

    data = request.get_json()
    message = Validation.isProductDataValid(data)
    if message!="":
        logging.error("Error:"+message)
        return {"message":message},400
    
    name = data.get("name")
    description =  data.get("description")
    sku =  data.get("sku")
    manufacturer = data.get("manufacturer")
    quantity = data.get("quantity")
    is_updated = False
    if sku is not None:
        is_product_already_present = Products.query.filter_by(sku=sku).first()
        is_sku_of_same_product = Products.query.filter_by(id=productId).first()
        if sku == is_sku_of_same_product.sku:
            product.sku = sku
        elif is_product_already_present:
            logging.error("Error:"+'Product with same sku already exist')
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
    logging.info("INFO:"+'Update Product API ended')
    return {},204

@app.route('/v1/product/<productId>', methods =['PATCH'])
def replace_product_details(productId):
    c.incr('Update_Product_Patch')
    logging.info("INFO:"+'Update Product API using PATCH started')
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        logging.error("Error:"+message)
        return {"message":message},401
    username_from_user, password_from_user = Encryption.decode(header)
    
    user = Users.query.filter_by(username=username_from_user).first()
    if user is None:
        logging.error("Error:"+'Invalid Credentials')
        return {"message":"Invalid Credentials"},401
    elif not Encryption.isValidPassword(password_from_user,user.password):
        logging.error("Error:"+'Invalid Credentials')
        return {"message": "Invalid Credentials"},401

    product = Products.query.filter_by(id=productId).first()
    if product is not None and product.owner_user_id!=user.id:
        logging.error("Error:"+'Forbidden')
        return {"message":"Forbidden"},403
    elif product is None:
        logging.error("Error:"+'Product Not Found')
        return {"message":"Product Not Found"},404

    data = request.get_json()
    if any(k not in ("name","description","sku", "manufacturer", "quantity") for k in data.keys()):
        logging.error("Error:"+'Updated restricted to name, description, sku, manufacturer, quantity only')
        return {"message":"Updated restricted to name, description, sku, manufacturer, quantity only"},400
    if data.get("name") == "" or data.get("description") == "" or data.get("sku") == "" or data.get("manufacturer") == "" or data.get("quantity") == "":
        logging.error("Error:"+'Fields cannot be empty')
        return {"message":"Fields cannot be empty"},400
    
    name = data.get("name")
    description =  data.get("description")
    sku =  data.get("sku")
    manufacturer = data.get("manufacturer")
    quantity = data.get("quantity")
    is_updated = False
    if sku is not None:
        if  not isinstance("test",type(sku)):
            logging.error("Error:"+'Invalid datatype : name, description, sku, manufacturer can only contain characters')
            return {"message":"Invalid datatype : name, description, sku, manufacturer can only contain characters"},400
        else:
            is_product_already_present = Products.query.filter_by(sku=sku).first()
            is_sku_of_same_product = Products.query.filter_by(id=productId).first()
            if sku == is_sku_of_same_product.sku:
                product.sku = sku
            elif is_product_already_present:
                logging.error("Error:"+'Invalid datatype : name, description, sku, manufacturer can only contain characters')
                return {"message":"Product with same sku already exist"},400
            else:
                is_updated = True
                product.sku = sku
    if name is not None:
        if  not isinstance("test",type(name)):
            logging.error("Error:"+'Invalid datatype : name, description, sku, manufacturer can only contain characters')
            return {"message":"Invalid datatype : name, description, sku, manufacturer can only contain characters"},400
        else:
            is_updated = True
            product.name = name 
    if description is not None:
        if  not isinstance("test",type(description)):
            logging.error("Error:"+'Invalid datatype : name, description, sku, manufacturer can only contain characters')
            return {"message":"Invalid datatype : name, description, sku, manufacturer can only contain characters"},400
        else:
            is_updated = True
            product.description = description
    if manufacturer is not None:
        if  not isinstance("test",type(manufacturer)):
            logging.error("Error:"+'Invalid datatype : name, description, sku, manufacturer can only contain characters')
            return {"message":"Invalid datatype : name, description, sku, manufacturer can only contain characters"},400
        else:
            is_updated = True
            product.manufacturer = manufacturer
    if quantity is not None:
        temp_int=1
        temp_float=1.0
        if type(temp_float)==type(quantity):
            if abs(int(quantity)-quantity)!=0:
                logging.error("Error:"+'Quantity cannot contain floating values')
                return {"message" : "Quantity cannot contain floating values"},400
            elif int(quantity)<0:
                logging.error("Error:"+'Quantity cannot be negative')
                return {"message" : "Quantity cannot be negative"},400
            elif int(quantity)>100:
                logging.error("Error:"+'Quantity cannot be greater than 100')
                return {"message" : "Quantity cannot be greater than 100"},400
        elif type(temp_int)!=type(quantity):
            logging.error("Error:"+'Quantity should be an integer')
            return {"message" : "Quantity should be an integer"},400
        elif quantity<0:
            logging.error("Error:"+'Quantity cannot be negative')
            return {"message" : "Quantity cannot be negative"},400
        elif quantity>100:
            logging.error("Error:"+'Quantity cannot be greater than 100')
            return {"message" : "Quantity cannot be greater than 100"},400
        else:
            is_updated = True
            product.quantity = int(quantity)
    if is_updated:
        product.date_last_updated = datetime.now()
        db.session.commit()
    logging.info("INFO:"+'Update Product API using PATCH ended')
    return {},204

@app.route('/v1/product/<productId>', methods =['DELETE'])
def delete_product(productId):
    c.incr('Delete_Product')
    logging.info("INFO:"+'Delete Product API started')
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        logging.error("Error:"+message)
        return {"message":message},401
    username_from_user, password_from_user = Encryption.decode(header)
    user = Users.query.filter_by(username=username_from_user).first()
    if user is None:
        logging.error("Error:"+'Invalid Credentials')
        return {"message":"Invalid Credentials"},401
    elif not Encryption.isValidPassword(password_from_user,user.password):
        logging.error("Error:"+'Invalid Credentials')
        return {"message": "Invalid Credentials"},401

    product = Products.query.filter_by(id=productId).first()
    if product is not None and product.owner_user_id!=user.id:
        logging.error("Error:"+'Forbidden')
        return {"message":"Forbidden"},403
    elif product is None:
        logging.error("Error:"+'Product Not Found')
        return {"message":"Product Not Found"},404
    
    db.session.delete(product)
    db.session.commit()
    logging.info("INFO:"+'Delete Product API ended')
    return {},204


@app.route("/v1/product/<productId>/image", methods=["GET"])
def get_all_files(productId):
    c.incr('Get_Images')
    logging.info("INFO:"+'Get Product Images API started')
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        logging.error("Error:"+message)
        return {"message":message},401
    username_from_user, password_from_user = Encryption.decode(header)
    user = Users.query.filter_by(username=username_from_user).first()
    if user is None:
        logging.error("Error:"+'Invalid Credentials')
        return {"message":"Invalid Credentials"},401
    elif not Encryption.isValidPassword(password_from_user,user.password):
        logging.error("Error:"+'Invalid Credentials')
        return {"message": "Invalid Credentials"},401

    product = Products.query.filter_by(id=productId).first()
    if product is not None and product.owner_user_id!=user.id:
        logging.error("Error:"+'Forbidden')
        return {"message":"Forbidden"},403
    elif product is None:
        logging.error("Error:"+'Product Not Found')
        return {"message":"Product Not Found"},404

    images = ProductImage.query.filter_by(product_id=productId)
    if images.first() is None:
        logging.error("Error:"+'No Image exist')
        return {"message":"No Image exist"},404
    schema = []
    for image in images:
        temp ={
        "image_id": image.id,
        "product_id": image.product_id,
        "file_name": image.file_name,
        "date_created": image.date_created,
        "s3_bucket_path": image.s3_bucket_path
        }
        schema.append(temp)
    logging.info("INFO:"+'Get Product Images API ended')
    return schema,200

@app.route("/v1/product/<productId>/image/<imageId>", methods=["GET"])
def get_file(productId,imageId):
    c.incr('Get_Image')
    logging.info("INFO:"+'Get Product Image using Image_ID API started')
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        logging.error("Error:"+message)
        return {"message":message},401
    username_from_user, password_from_user = Encryption.decode(header)
    user = Users.query.filter_by(username=username_from_user).first()
    if user is None:
        logging.error("Error:"+'Invalid Credentials')
        return {"message":"Invalid Credentials"},401
    elif not Encryption.isValidPassword(password_from_user,user.password):
        logging.error("Error:"+'Invalid Credentials')
        return {"message": "Invalid Credentials"},401

    product = Products.query.filter_by(id=productId).first()
    print(product is not None)
    if product is not None and product.owner_user_id!=user.id:
        logging.error("Error:"+'Forbidden')
        return {"message":"Forbidden"},403
    elif product is None:
        logging.error("Error:"+'Product Not Found')
        return {"message":"Product Not Found"},404

    image = ProductImage.query.filter_by(id=imageId).first()
    print(image is not None)
    if image is not None and image.product_id!=int(productId):
        logging.error("Error:"+'Forbidden')
        return {"message":"Forbidden"},403
    elif image is None:
        logging.error("Error:"+'Image not Found')
        return {"message":"Image not Found"},404

    schema = {
        "id" : image.id,
        "product_id" : image.product_id,
        "file_name" : image.file_name,
        "date_created" : image.date_created,
        "s3_bucket_path" : image.s3_bucket_path
    }
    logging.info("INFO:"+'Get Product Image using Image_ID API ended')
    return schema, 200


@app.route("/v1/product/<productId>/image", methods=["POST"])
def upload_file(productId):
    c.incr('Upload_Image')
    logging.info("INFO:"+'Upload Product Image API started')
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        logging.error("Error:"+message)
        return {"message":message},401
    username_from_user, password_from_user = Encryption.decode(header)
    user = Users.query.filter_by(username=username_from_user).first()
    if user is None:
        logging.error("Error:"+'Invalid Credentials')
        return {"message":"Invalid Credentials"},401
    elif not Encryption.isValidPassword(password_from_user,user.password):
        logging.error("Error:"+'Invalid Credentials')
        return {"message": "Invalid Credentials"},401

    product = Products.query.filter_by(id=productId).first()
    if product is not None and product.owner_user_id!=user.id:
        logging.error("Error:"+'Forbidden')
        return {"message":"Forbidden"},403
    elif product is None:
        logging.error("Error:"+'Product Not Found')
        return {"message":"Product Not Found"},404

    # Logic to upload images
    files = request.files
    if len(files)==0:
        logging.error("Error:"+'No Files to Upload')
        return {"message":"Nothing to Upload"},400
    
    for item in files.items(multi=True):
        if item[0].strip()=='':
            logging.error("Error:"+'Keys cannot be blank')
            return {"message":"Keys cannot be blank"},400
        elif item[1].filename=="":
            logging.error("Error:"+'File not selected to upload')
            return {"message":f"Please select file to upload for {item[0]}"},400
        elif imghdr.what(item[1]) is None:
            logging.error("Error:"+'Only Images are allowed to be uploaded')
            return {"message":"Only Images are allowed to be uploaded"},400
    schema=[]
    for item in files.items(multi=True):
        file = item[1]
        unique_Id = uuid.uuid4()
        file_name = file.filename
        location = f"u_{product.owner_user_id}/p_{productId}/{unique_Id}/{file_name}"
        output = upload_file_to_s3(file,location,app.config['S3_BUCKET'])
        if output!="Upload Successful":
            logging.error("Error:"+'Error at S3')
            return {"message":"Error at s3"},400
        image = ProductImage(product_id=productId,file_name=file_name,s3_bucket_path=location)
        db.session.add(image)
        db.session.commit()
        image = ProductImage.query.filter_by(s3_bucket_path=location).first()
        temp = {
            "id" : image.id,
            "product_id" : image.product_id,
            "file_name" : image.file_name,
            "date_created" : image.date_created,
            "s3_bucket_path" : image.s3_bucket_path
        }
        schema.append(temp)
    logging.info("INFO:"+'Upload Product Image API ended')
    return schema,201

@app.route("/v1/product/<productId>/image/<imageId>", methods=["DELETE"])
def delete_file(productId,imageId):
    c.incr('Delete_Image')
    logging.info("INFO:"+'Delete Product Image API started')
    header = request.headers
    message =  Validation.isUserValid(header)
    if message != "":
        logging.error("Error:"+message)
        return {"message":message},401
    username_from_user, password_from_user = Encryption.decode(header)
    user = Users.query.filter_by(username=username_from_user).first()
    if user is None:
        logging.error("Error:"+'Invalid Credentials')
        return {"message":"Invalid Credentials"},401
    elif not Encryption.isValidPassword(password_from_user,user.password):
        logging.error("Error:"+'Invalid Credentials')
        return {"message": "Invalid Credentials"},401

    product = Products.query.filter_by(id=productId).first()
    if product is not None and product.owner_user_id!=user.id:
        logging.error("Error:"+'Forbidden')
        return {"message":"Forbidden"},403
    elif product is None:
        logging.error("Error:"+'Product Not Found')
        return {"message":"Product Not Found"},404

    image = ProductImage.query.filter_by(id=imageId).first()
    if image is not None and image.product_id!=int(productId):
        logging.error("Error:"+'Forbidden')
        return {"message":"Forbidden"},403
    elif image is None:
        logging.error("Error:"+'Image not Found')
        return {"message":"Image not Found"},404

    output = delete_object_from_s3(image.s3_bucket_path,app.config['S3_BUCKET'])
    if output!="Delete Successful":
        logging.error("Error:"+'Error at s3')
        return {"message":"Error at s3"},400
    db.session.delete(image)
    db.session.commit()
    logging.info("INFO:"+'Delete Product Image API ended')
    return {},204


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)