import unittest
from app import validation, app

class WebAppTest(unittest.TestCase):

    #check for response 200
    def test_validation_function(self):
        self.assertEqual(validation("abc", "xyz", "abc@gmail.com", "kljh"), "")
        self.assertEqual(validation("abc", "xyz", "abcgail.com", "kljh"), 'Username should contain email address in correction format (example: demo@domain.com)')

    def test_index(self):
        tester = app.test_client(self)
        response = tester.get("/healthz")
        statuscode = response.status_code
        self.assertEqual(statuscode,200)
    

if __name__ == "__main__":
    unittest.main()