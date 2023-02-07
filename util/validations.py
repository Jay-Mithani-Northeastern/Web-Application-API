import re
class Validation():
    def isUserDataValid(data):
        message=""
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        username = data.get("username")
        password = data.get("password")
        is_username_valid = r'^(?i)([a-z0-9]+([/.][a-z0-9]+)?[@][a-z0-9]+[/.][a-z]+)$'
        mandatory = ["first_name","last_name","username","password"]
        if any(k not in data.keys() for k in mandatory):
            message = "Mandatory fields : first_name, last_name, username, password"
        elif len(data)>4:
            message = "Restricted : Only first_name, last_name, username, password fields are allowed"
        elif first_name == "" or last_name == "" or username == "" or password == "":
            message = "Values cannot be Null : first_name, last_name, username, password"
        elif not(re.match(is_username_valid,username)):
            message = "Username should contain email address in correction format (example: demo@domain.com)"
        return message
    
    def isProductDataValid(data):
        message = ""
        name = data.get("name")
        description = data.get("description")
        sku = data.get("sku")
        manufacturer = data.get("manufacturer")
        quantity = data.get("quantity")
        mandatory = ["name","description","sku","manufacturer","quantity"]

        is_number = r'^\d+$'
        if any(k not in data.keys() for k in mandatory):
            message = "Mandatory fields : name, description, sku, manufacturer, quantity"
        elif len(data)>5:
            message = "Restricted : Only name, description, sku, manufacturer, quantity fields are allowed"
        elif name=="" or description=="" or sku=="" or manufacturer=="" or quantity=="":
            message = "Values cannot be Null : name, description, sku, manufacturer, quantity"
        elif not(re.match(is_number,quantity)) or int(quantity)<1:
            message = "Quantity should be an integer > 0"
        
        return message
        
        



    def isUserValid(data):
        message = ""
        if "Authorization" not in data:
            message = "Please enter credentials"
        return message

