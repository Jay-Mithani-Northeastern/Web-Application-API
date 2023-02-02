import unittest
from app import app


class WebAppTest(unittest.TestCase):

    #check for response 200
    def test_index(self):
        tester = app.test_client(self)
        response = tester.get("/healthz")
        statuscode = response.status_code
        self.assertEqual(statuscode,200)

if __name__ == "__main__":
    unittest.main()