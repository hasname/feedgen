from django.test import Client, TestCase

class IndexTestCase(TestCase):
    def test_index(self):
        c = Client()
        res = c.get('/')
        self.assertRedirects(res, 'https://github.com/hasname/feedgen', fetch_redirect_response=False)
