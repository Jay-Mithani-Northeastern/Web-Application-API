import unittest
from app import validation

class WebAppTest(unittest.TestCase):

    #check for response 200
    def test_validation_function(self):
        self.assertEqual(validation("abc", "xyz", "abc@gmail.com", "kljh"), "")
        self.assertEqual(validation("abc", "xyz", "abcgail.com", "kljh"), 'Username should contain email address in correction format (example: demo@domain.com)')

    

if __name__ == "__main__":
    unittest.main()