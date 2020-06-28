from django.test import Client, TestCase

class RobotstxtTestCase(TestCase):
    def test_robotstxt(self):
        c = Client()
        res = c.get('/robots.txt')
        self.assertEqual(res.status_code, 200)
