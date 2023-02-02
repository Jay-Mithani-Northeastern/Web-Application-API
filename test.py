
try:
    from app import app
    import unittest

except Exception as e:
    print("Some Modules are missing {}".format(e))


class WebAppTest(unittest.TestCase):

    #check for response 200
    def test_index(self):
        tester = app.test_client(self)
        response = tester.get("/healthz")
        statuscode = response.status_code
        self.assertEqual(statuscode,200)

if __name__ == "__main__":
    unittest.main()