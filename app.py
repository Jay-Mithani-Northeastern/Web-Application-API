import os
import datetime
import re
import base64
from dotenv import load_dotenv
from flask import Flask, request
import psycopg2
import bcrypt

CREATE_USERS_TABLE = """CREATE TABLE IF NOT EXISTS users 
    (id SERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    password TEXT NOT NULL,
    user_name Text NOT NULL,
    account_created TIMESTAMP NOT NULL,
    account_updated TIMESTAMP NOT NULL);
"""

INSERT_USER_RETURN_ID = """ 
    INSERT INTO users (first_name, last_name, password, user_name, account_created,account_updated)
    VALUES 
    (%s,%s,%s,%s,%s,%s) RETURNING id;
"""
#Connection to load env variables and connect to db using psycopg2
load_dotenv()
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
url = os.getenv("DATABASE_URL")

# End Point to check server status
@app.get("/healthz")
def get_healthz():
    return {"message ": "Endpoint is Healthy"}, 200

# Endpoint to create user
@app.post("/v1/user")
def create_user():
    data = request.get_json()
    connection = psycopg2.connect(url)
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    password = data.get("password")
    username = data.get("username")

    message = validation(first_name, last_name, username, password)
    if message != "":
        return {'message': message}, 400

    encrypted_password = bcrypt.hashpw(
        password.encode('utf-8'), bcrypt.gensalt())
    encrypted_password = encrypted_password.decode('utf-8')
    account_created = datetime.datetime.today()
    account_updated = datetime.datetime.today()
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_USERS_TABLE)
            cursor.execute(
                "SELECT * FROM users WHERE user_name = %s", (username,))
            user = cursor.fetchone()
            if user:
                connection.commit()
                cursor.close()
                return {'message': 'User with this email already exists'}, 400
            else:
                cursor.execute(CREATE_USERS_TABLE)
                cursor.execute(INSERT_USER_RETURN_ID, (first_name, last_name,
                               encrypted_password, username, account_created, account_updated))
                user_id = cursor.fetchone()[0]
                connection.commit()
                cursor.close()
    schema = {
        "id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "account_created": account_created,
        "account_updated": account_updated
    }
    return schema, 201

# Endpoint to fetch user details
@app.get(f"/v1/user/<userId>")
def get_user_details(userId):
    header = request.headers
    message = ""
    if "Authorization" not in header:
        message = "Please enter credentials"
        return {"message":message}, 401
    
    connection = psycopg2.connect(url)
    key = base64.b64decode(header.get("Authorization").split(" ")[1])
    user_data = key.decode().split(":")
    user_name, password = user_data[0], user_data[1]
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_USERS_TABLE)
            cursor.execute(
                "SELECT * FROM users WHERE id = %s", (userId,))
            user = cursor.fetchone()
            if user is None:
                message = "Forbidden"
                connection.commit()
                cursor.close()
                return {'message': message}, 403
            else:
                cursor.execute("SELECT user_name,password FROM users WHERE id = %s", (userId,))
                user_data = cursor.fetchone()
                username_from_db = user_data[0]
                password_from_db = user_data[1]
                if not bcrypt.checkpw(password.encode('utf-8'),password_from_db.encode('utf-8')) or username_from_db!=user_name:
                    message = "Invalid Credentials entered"
                    connection.commit()
                    cursor.close()
                    return {"message":message}, 401
                else:
                    cursor.execute("SELECT first_name,last_name,user_name,account_created,account_updated FROM users WHERE id = %s", (userId,))
                    user_data = cursor.fetchone()
                    first_name = user_data[0]
                    last_name = user_data[1]
                    user_name = user_data[2]
                    account_created = user_data[3]
                    account_updated = user_data[4]
                    connection.commit()
                    cursor.close()
    schema = {
        "id": userId,
        "first_name": first_name,
        "last_name": last_name,
        "username": user_name,
        "account_created": account_created,
        "account_updated": account_updated
    } 
    return schema,200

# Endpoint to update user details
@app.put(f"/v1/user/<userId>")
def update_user_details(userId):
    header = request.headers
    message = ""
    if "Authorization" not in header:
        message = "Please enter credentials"
        return {"message":message}, 401
    
    connection = psycopg2.connect(url)
    key = base64.b64decode(header.get("Authorization").split(" ")[1])
    user_data = key.decode().split(":")
    user_name, password = user_data[0], user_data[1]
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_USERS_TABLE)
            cursor.execute(
                "SELECT * FROM users WHERE id = %s", (userId,))
            user = cursor.fetchone()
            if user is None:
                message = "Forbidden"
                connection.commit()
                cursor.close()
                return {'message': message}, 403
            else:
                cursor.execute("SELECT user_name,password FROM users WHERE id = %s", (userId,))
                user_data = cursor.fetchone()
                username_from_db = user_data[0]
                password_from_db = user_data[1]
                if not bcrypt.checkpw(password.encode('utf-8'),password_from_db.encode('utf-8')) or username_from_db!=user_name:
                    message = "Invalid Credentials entered"
                    connection.commit()
                    cursor.close()
                    return {"message":message}, 401
                else:
                    data = request.get_json()
                    any_other_field =  any(k not in ("first_name","last_name","password") for k in data.keys())

                    new_first_name = data.get("first_name")
                    new_last_name = data.get("last_name")
                    new_username = data.get("username")
                    new_password = data.get("password")

                    if any_other_field:
                        connection.commit()
                        cursor.close()
                        return {"message" : "Update restricted ! Only update on first_name, last_name, password is allowed"},400
                    elif new_first_name is None and new_last_name is None and new_username is None and new_password is None:
                        connection.commit()
                        cursor.close()
                        return {},204
                    else:
                        today = datetime.datetime.today()
                        if new_first_name:
                            cursor.execute("UPDATE users SET first_name = %s WHERE id = %s", (new_first_name,userId))
                        if new_last_name:
                            cursor.execute("UPDATE users SET last_name = %s WHERE id = %s", (new_last_name,userId))
                        if new_password:
                            encrypted_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                            encrypted_password = encrypted_password.decode('utf-8')
                            cursor.execute("UPDATE users SET password = %s WHERE id = %s", (encrypted_password,userId))
                        cursor.execute("UPDATE users SET account_updated = %s WHERE id = %s", (today,userId))
                        connection.commit()
                        cursor.close()
    return {},204



# Function to perform validation
def validation(first_name, last_name, username, password):
    message = ""
    contains_number = r'.*[0-9]'
    is_username_valid = r'^(?i)([a-z0-9]+([/.][a-z0-9]+)?[@][a-z0-9]+[/.][a-z]+)$'
    if first_name == "" or last_name == "" or username == "" or password == "":
        message = "Value cannot be Null"
    elif re.match(contains_number, first_name):
        message = "First name should only contain characters"
    elif re.match(contains_number, last_name):
        message = "Last name should only contain characters"
    elif not(re.match(is_username_valid,username)):
        message = "Username should contain email address in correction format (example: demo@domain.com)"
    
    return message

if __name__ == '__main__':
    app.run()