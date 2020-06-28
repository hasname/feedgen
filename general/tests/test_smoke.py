from django.test import Client, TestCase

class SmokeTestCase(TestCase):
    def test_job104(self):
        c = Client()
        res = c.get('/104/test')
        self.assertEqual(res.status_code, 200)
