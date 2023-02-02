
# Web Application

Steps to install dependencies and libraries:
1. Create Virtual Environment inside WEBAPPP folder\
   Command: "python3 -m venv .environment"
2. Activate Virtual Environment\
   Command: "source .environment/bin/activate"
3. Install dependencies from requirement.txt file\
   Command: "pip install -r requirements.txt"

File to create before running the app:
1. ".env" file containing:\
   DATABASE_URL = URL
   URL in format "DATABASE_URL = postgresql://username:password@localhost:port/database_name"

Features:
The webapp contains 4 endpoints:

1. /healthz
   - Return "200" if endpoint is working

2. /v1/users
   - API to create user which takes below fields as input payload from user:
     - first_name
     - last_name
     - username
     - password
   - account_created and account_updated field automatically fetches present date and time
   - user is allowed to change account_created and account_updated field
   - username field is unique
   - password is encrypted using bcrypt and salt before storing in database
   - return's "400" if incorrect data is passed, else return's "201" stating user is successfully created in database

3. /v1/users/{userId}
   - API to fetch user details
   - check if user is authenticated of not
   - if unauthorized, return 401-Unauthorized
   - else if authentication is successful and userId is incorrect, return 403-Forbidden
   - else return 200 and JSON payload with fields: id, first_name, last_name, username, account_created, account_updated
   
4. /v1/users/{userId}
   - API to update user details
   - User can only update this fields: first_name, last_name, password
   - If there is any field updated, update the account_updated field with present time
   - if unauthorized, return 401-Unauthorized
   - else if incorrect payload provided,return 400-Bad request
   - else if authentication is successful and userId is incorrect, return 403-Forbidden
   - else return 204-No content 
   
# Testing Pull request status check