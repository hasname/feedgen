from django.test import Client, TestCase
import os
import re
import requests_mock

class SmokeTestCase(TestCase):
    @requests_mock.mock()
    def test_bookwalker_lightnovel(self, m):
        text = open(os.path.dirname(__file__) + '/html_bookwalker_manga.txt').read()
        m.get('https://www.bookwalker.com.tw/block/3?order=sell_desc', text=text)

        c = Client()
        res = c.get('/bookwalker-manga')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_bookwalker_lightnovel(self, m):
        text = open(os.path.dirname(__file__) + '/html_bookwalker_lightnovel.txt').read()
        m.get('https://www.bookwalker.com.tw/block/5?order=sell_desc', text=text)

        c = Client()
        res = c.get('/bookwalker-lightnovel')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_cakeresume(self, m):
        text = open(os.path.dirname(__file__) + '/html_cakeresume.txt').read()
        m.get('https://www.cakeresume.com/jobs/test?location_list%5B0%5D=Taiwan&order=latest', text=text)

        c = Client()
        res = c.get('/cakeresume/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_dcard_board(self, m):
        text = open(os.path.dirname(__file__) + '/html_dcard_board.txt').read()
        m.get('https://www.dcard.tw/f/moon', text=text)

        c = Client()
        res = c.get('/dcard/board/moon')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_dcard_main(self, m):
        m.get('https://www.dcard.tw/service/api/v2/popularForums/GetHead?listKey=popularForums', text='{"listKey":"popularForums","head":"00000000-0000-0000-0000-000000000000"}')

        text = open(os.path.dirname(__file__) + '/json_dcard_popular.txt').read()
        m.get('https://www.dcard.tw/service/api/v2/popularForums/GetPage?pageKey=00000000-0000-0000-0000-000000000000', text=text)

        c = Client()
        res = c.get('/dcard/main')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_job104(self, m):
        text = open(os.path.dirname(__file__) + '/json_job104.txt').read()
        m.get(re.compile('^https://www\.104\.com\.tw/jobs/search/api/jobs', text=text))

        c = Client()
        res = c.get('/104/test')
        self.assertEqual(res.status_code, 200)

        res = c.get('/104company/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_job1111(self, m):
        text = open(os.path.dirname(__file__) + '/html_job1111.txt').read()
        m.get('https://www.1111.com.tw/search/job?col=da&ks=test&page=1&sort=desc', text=text)

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
    def test_meetjobs(self, m):
        text = open(os.path.dirname(__file__) + '/json_meetjobs.txt').read()
        m.get('https://api.meet.jobs/api/v1/jobs?page=1&order=update&q=test&include=required_skills&external_job=true', text=text)

        c = Client()
        res = c.get('/meetjobs/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_momoshop(self, m):
        m.get('https://www.momoshop.com.tw/', text='')

        text = open(os.path.dirname(__file__) + '/json_momoshop.txt').read()
        m.post('https://www.momoshop.com.tw/ajax/ajaxTool.jsp?n=2018', text=text)

        c = Client()
        res = c.get('/momoshop/test')
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
    def test_plurk_search(self, m):
        text = open(os.path.dirname(__file__) + '/json_plurk_search.txt').read()
        m.post('https://www.plurk.com/Search/search2', text=text)

        c = Client()
        res = c.get('/plurk/search/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_plurk_top(self, m):
        text = open(os.path.dirname(__file__) + '/json_plurk_top_zh.txt').read()
        m.get('https://www.plurk.com/Stats/topReplurks?period=day&lang=zh&limit=10', text=text)

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
        m.get('https://shopee.tw/api/v4/search/search_items/?by=ctime&keyword=test&limit=60&newest=0&order=desc&page_type=search&scenario=PAGE_GLOBAL_SEARCH&version=2', text=text)

        c = Client()
        res = c.get('/shopee/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_taipeimetrotimetable(self, m):
        text = open(os.path.dirname(__file__) + '/html_taipeimetrotimetable.txt').read()
        m.get('https://web.metro.taipei/img/ALL/timetables/079a.PDF', headers={'last-modified': 'Fri, 11 Nov 2022 16:20:50 GMT'}, text=text)

        c = Client()
        res = c.get('/taipeimetrotimetable/079a')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_yourator(self, m):
        text = open(os.path.dirname(__file__) + '/json_yourator.txt').read()
        m.get('https://www.yourator.co/api/v2/jobs?term[]=test', text=text)

        c = Client()
        res = c.get('/yourator/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_youtube(self, m):
        text = open(os.path.dirname(__file__) + '/html_youtube.txt').read()
        m.get('https://www.youtube.com/results?search_query=test&sp=CAI%253D', text=text)

        c = Client()
        res = c.get('/youtube/test')
        self.assertEqual(res.status_code, 200)
