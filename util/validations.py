import re
class Validation():
    def isUserDataValid(data):
        message=""
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        username = data.get("username")
        password = data.get("password")
        is_username_valid = r'^(?i)([a-z0-9]+([/.][a-z0-9]+)?[@][a-z0-9]+[/.][a-z]+)$'
        is_name_valid = r'^(?i)[a-z]+$'
        mandatory = ["first_name","last_name","username","password"]
        if any(k not in data.keys() for k in mandatory):
            message = "Mandatory fields : first_name, last_name, username, password"
        elif len(data)>4:
            message = "Restricted : Only first_name, last_name, username, password fields are allowed"
        elif first_name == "" or last_name == "" or username == "" or password == "":
            message = "Values cannot be Null : first_name, last_name, username, password"
        elif any(not isinstance("Temp",type(k)) for k in data.values()):
            message = "first_name, last_name, username, password should contain string"
        elif not(re.match(is_name_valid,first_name)) or not(re.match(is_name_valid,last_name)):
            message = "first_name and last_name should can only contain characters and should be of one word without spaces"
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
        temp_int=1
        temp_float=1.0
        temp_string = "temp"
        if any(k not in data.keys() for k in mandatory):
            message = "Mandatory fields : name, description, sku, manufacturer, quantity"
        elif len(data)>5:
            message = "Restricted : Only name, description, sku, manufacturer, quantity fields are allowed"
        elif name=="" or description=="" or sku=="" or manufacturer=="" or quantity=="":
            message = "Values cannot be Null : name, description, sku, manufacturer, quantity"
        elif not isinstance(temp_string,type(name)) or not isinstance(temp_string,type(description)) or not isinstance(temp_string,type(sku)) or not isinstance(temp_string,type(manufacturer)):
            message = "Invalid datatype : name, description, sku, manufacturer can only contain characters"
        elif isinstance(temp_float,type(quantity)):
            if abs(int(quantity)-quantity)!=0:
                message = "Quantity cannot contain floating values"
            elif int(quantity)<0:
                message = "Quantity cannot be negative"
        elif not isinstance(temp_int,type(quantity)):
            message = "Quantity should be an integer"
        elif quantity<0:
            message = "Quantity cannot be negative"
        
        return message

    def isUserValid(data):
        message = ""
        if "Authorization" not in data:
            message = "Please enter credentials"
        return message

