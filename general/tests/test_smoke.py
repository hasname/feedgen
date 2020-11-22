from django.test import Client, TestCase
import os
import re
import requests_mock

class SmokeTestCase(TestCase):
    @requests_mock.mock()
    def test_bookwalker_lightnovel(self, m):
        text = open(os.path.dirname(__file__) + '/html_bookwalker_lightnovel.txt').read()
        m.get('https://www.bookwalker.com.tw/more/fiction/1/3', text=text)

        c = Client()
        res = c.get('/bookwalker-lightnovel')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_cakeresume(self, m):
        text = open(os.path.dirname(__file__) + '/html_cakeresume.txt').read()
        m.get('https://www.cakeresume.com/jobs?q=php', text=text)

        c = Client()
        res = c.get('/cakeresume/php')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_dcard_main(self, m):
        text = open(os.path.dirname(__file__) + '/html_dcard_main.txt').read()
        m.get('https://www.dcard.tw/f', text=text)

        c = Client()
        res = c.get('/dcard/main')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_job104(self, m):
        text = open(os.path.dirname(__file__) + '/html_job104.txt').read()
        m.get('https://www.104.com.tw/jobs/search/?ro=0&kwop=7&keyword=test&order=11&asc=0&page=1&mode=s', text=text)

        c = Client()
        res = c.get('/104/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_job1111(self, m):
        text = open(os.path.dirname(__file__) + '/html_job1111.txt').read()
        m.get('https://www.1111.com.tw/search/job?flag=13&ks=test&fs=1&si=1&ts=4&col=da&sort=desc', text=text)

        c = Client()
        res = c.get('/1111/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_job518(self, m):
        text = open(os.path.dirname(__file__) + '/html_job518.txt').read()
        m.get('https://www.518.com.tw/job-index-P-1.html?i=1&am=1&ad=test&orderType=1&orderField=8', text=text)

        c = Client()
        res = c.get('/518/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_pchome(self, m):
        text = open(os.path.dirname(__file__) + '/json_pchome.txt').read()
        m.get('https://ecshweb.pchome.com.tw/search/v3.3/all/results?q=test&page=1&sort=new/dc', text=text)

        c = Client()
        res = c.get('/pchome/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_pchome_lightnovel(self, m):
        text = open(os.path.dirname(__file__) + '/json_pchome_lightnovel.txt').read()
        m.get('https://ecapi.pchome.com.tw/cdn/ecshop/prodapi/v2/newarrival/DJAZ/prod&offset=1&limit=20&fields=Id,Nick,Pic,Price,Discount,isSpec,Name,isCarrier,isSnapUp,isBigCart&_callback=jsonp_prodlist?_callback=jsonp_prodlist', text=text)

        c = Client()
        res = c.get('/pchome-lightnovel')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_plurk(self, m):
        text = open(os.path.dirname(__file__) + '/json_plurk_top_zh.txt').read()
        m.get('https://www.plurk.com/Stats/topReplurks?period=day&lang=zh&limit=20', text=text)

        c = Client()
        res = c.get('/plurk/top/zh')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_rent591(self, m):
        text = open(os.path.dirname(__file__) + '/html_rent591.txt').read()
        m.get('https://rent.591.com.tw/?kind=0&order=posttime&orderType=desc&region=1&keywords=abc', text=text)

        c = Client()
        res = c.get('/rent591/1/abc')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_shopee(self, m):
        text = open(os.path.dirname(__file__) + '/json_shopee.txt').read()
        m.get('https://shopee.tw/api/v2/search_items/?by=ctime&keyword=test&limit=50&newest=0&order=desc&page_type=search', text=text)

        text = open(os.path.dirname(__file__) + '/json_shopee_item.txt').read()
        m.get(re.compile('https://shopee.tw/api/v2/item/get'), text=text)

        text = open(os.path.dirname(__file__) + '/json_shopee_shop.txt').read()
        m.get(re.compile('https://shopee.tw/api/v2/shop/get'), text=text)

        c = Client()
        res = c.get('/shopee/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_youtube(self, m):
        text = open(os.path.dirname(__file__) + '/html_youtube.txt').read()
        m.get('https://www.youtube.com/results?sp=CAI%253D&search_query=test', text=text)

        c = Client()
        res = c.get('/youtube/test')
        self.assertEqual(res.status_code, 200)
