from django.test import Client, TestCase

class SmokeTestCase(TestCase):
    def test_job104(self):
        c = Client()
        res = c.get('/104/test')
        self.assertEqual(res.status_code, 200)

    def test_job1111(self):
        c = Client()
        res = c.get('/1111/test')
        self.assertEqual(res.status_code, 200)

    def test_job518(self):
        c = Client()
        res = c.get('/518/test')
        self.assertEqual(res.status_code, 200)

    def test_pchome(self):
        c = Client()
        res = c.get('/pchome/test')
        self.assertEqual(res.status_code, 200)

    def test_plurk(self):
        c = Client()
        res = c.get('/plurk/top/zh')
        self.assertEqual(res.status_code, 200)

    def test_shopee(self):
        c = Client()
        res = c.get('/shopee/test')
        self.assertEqual(res.status_code, 200)

    def test_shopee(self):
        c = Client()
        res = c.get('/youtube/test')
        self.assertEqual(res.status_code, 200)
