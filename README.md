
# Web Application

Steps to install dependencies and libraries:
1. Create Virtual Environment inside WEBAPPP folder\
   Command: "python3 -m venv .venv"
2. Activate Virtual Environment\
   Command: "source .venv/bin/activate"
3. Install dependencies from requirement.txt file\
   Command: "pip install -r requirements.txt"

File to create before running the app:
1. ".env" file containing:\
   DATABASE_URL = URL
   URL in format "DATABASE_URL = postgresql://username:password@localhost:port/database_name"

Features:
The webapp contains 4 endpoints:

1. /healthz - GET
   - Return "200" if endpoint is working

2. /v1/user - POST
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

3. /v1/user/{userId} - GET
   - API to fetch user details
   - check if user is authenticated of not
   - if unauthorized, return 401-Unauthorized
   - else if authentication is successful and userId is incorrect, return 403-Forbidden
   - else return 200 and JSON payload with fields: id, first_name, last_name, username, account_created, account_updated
   
4. /v1/user/{userId} - PUT
   - API to update user details
   - User can only update this fields: first_name, last_name, password
   - If there is any field updated, update the account_updated field with present time
   - if unauthorized, return 401-Unauthorized
   - else if incorrect payload provided,return 400-Bad request
   - else if authentication is successful and userId is incorrect, return 403-Forbidden
   - else return 204-No content 

5.  /v1/product - POST
   - API to add product which takes below fields as input payload from user:
     - name
     - description
     - sku
     - manufacturer
     - quantity
   - Only user will valid credentials can create and add a product
   - account_created and account_updated field automatically fetches present date and time of operation performed
   - owner_user_id which is foreign key field referenced to id of user table, automatically stores the user id who added the product
   - sku field is unique for each product listed
   - Validations are performed to check if quantity is an integer and non-negative number

6. /v1/product/{productId} - GET
   - API to fetch product details
   - return's 404 if product not found, else return's product details for requested productId

7. /v1/product/{productId} - PUT
   - API to update product details
   - Only the user owner who created the product, is allowed to update product details
   - All fields are mandatory to be passed in request payload

8. /v1/product/{productId} - PATCH
   - API to update product details
   - Only the user owner who created the product, is allowed to update product details
   - Only the fields which needs to be updated should be passed in request payload

9. /v1/product/{productId} - DELETE
   - API to delete product
   - Only the user owner who created the product, is allowed to delete the product

10. /v1/product/<productId>/image - GET
   - API to fetch all images details of a single product

11. /v1/product/<productId>/image/<imageId> - GET
   - API to fetch a single image of a particular product
  
12. /v1/product/<productId>/image - POST
   - API to push image(s) of a particular product to S3 bucket

13. /v1/product/<productId>/image/<imageId> - DELETE
   - API to delete image of a product from S3 bucket

   
