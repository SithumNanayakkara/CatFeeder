import unittest
import sys

sys.path.extend(['/var/www/CatFeeder'])

from app import app

class TestApp(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Home Page', response.data)

    def test_feedbuttonclick(self):
        response = self.app.get('/feedbuttonclick')
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertIn(b'Feed success!', response.data)  # Assuming this message is displayed on success

    def test_admin_login_page(self):
        response = self.app.get('/adminLogin')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Admin Login', response.data)

    def test_invalid_login(self):
        response = self.app.post('/login', data={'usrname': 'invaliduser', 'psw': 'invalidpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid Credentials', response.data)

    def test_valid_login(self):
        response = self.app.post('/login', data={'usrname': 'validuser', 'psw': 'validpassword'})
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertIn(b'Admin Page', response.data)  # Assuming this message is displayed on success

# Add more test cases as needed

if __name__ == '__main__':
    unittest.main()