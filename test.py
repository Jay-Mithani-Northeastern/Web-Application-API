import unittest
from util import validations

class WebAppTest(unittest.TestCase):

    #check for response 200
    def test_validation_function(self):
        data1 = {
            "first_name" : "test",
            "last_name" : "demo",
            "username" :  "abc@gmail.com",
            "password" : "add"
        }
        data2 = {
            "first_name" : "test",
            "last_name" : "demo",
            "username" :  "abcgmail.com",
            "password" : "add"
        }
        self.assertEqual(validations.Validation.isUserValid(data1), "")
        self.assertEqual(validations.Validation.isUserValid(data2), "Username should contain email address in correction format (example: demo@domain.com)")

    

if __name__ == "__main__":
    unittest.main()