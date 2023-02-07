import bcrypt,base64
class Encryption():
    def encrypt(password):
        encrypted_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        return encrypted_password

    def decode(header):
        key = base64.b64decode(header.get("Authorization").split(" ")[1])
        user_data = key.decode().split(":")
        username, password = user_data[0], user_data[1]
        return username,password
        
    def isValidPassword(userpassword,dbpassword):
        isValid = bcrypt.checkpw(userpassword.encode('utf-8'),dbpassword.encode('utf-8'))
        return isValid
