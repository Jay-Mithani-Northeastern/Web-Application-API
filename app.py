import os
import datetime
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

load_dotenv()

app = Flask(__name__)
url = os.getenv("DATABASE_URL")
connection = psycopg2.connect(url)
print(connection)

@app.get("/api/healthz")
def get_healthz():
    return {"message ": "Healthy"},200

@app.post("/api/healthz")
def post_healthz():
    return {"message ": "Healthy"},200

@app.post("/v1/user")
def create_user():
    data = request.get_json()
    connection = psycopg2.connect(url)
    first_name = data["first_name"]
    last_name = data["last_name"]
    password = data["password"]
    username = data["username"]
    if first_name == "" or last_name=="" or username=="" or password=="":
        return {'message': 'Values cannot be null'}, 400

    encrypted_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    today = datetime.datetime.today()
    account_created = today
    account_updated = today
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE user_name = %s", (username,))
            user = cursor.fetchone()
            if user:
                return {'message': 'User with this email already exists'}, 400
            else:
                cursor.execute(CREATE_USERS_TABLE)
                cursor.execute(INSERT_USER_RETURN_ID, (first_name,last_name,encrypted_password,username,account_created,account_updated))
                user_id = cursor.fetchone()[0]
                print(cursor.fetchone())
    # connection.commit()
    # connection.close()
    schema = {
        "id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "account_created": today,
        "account_updated": today
    }
    
    return schema,201
