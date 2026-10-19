import re
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import lxml.etree
import lxml.html
import requests_mock
from django.test import Client, TestCase


class SmokeTestCase(TestCase):
    def assert_plurk_images(self, response):
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        feed = lxml.etree.fromstring(response.content)
        contents = feed.findall('atom:entry/atom:content', ns)
        self.assertTrue(contents)
        images = []
        for content in contents:
            self.assertEqual(content.get('type'), 'html')
            self.assertEqual(len(content), 0)
            body = lxml.html.fragment_fromstring(content.text or '', create_parent='div')
            images.extend(body.cssselect('img'))
        self.assertTrue(images)
        for img in images:
            self.assertRegex(img.get('src'), r'^https://')

    def assert_bookwalker_entries(self, response, first_title, first_url):
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'xhtml': 'http://www.w3.org/1999/xhtml',
        }
        feed = lxml.etree.fromstring(response.content)
        entries = feed.findall('atom:entry', ns)
        self.assertEqual(len(entries), 16)

        with self.subTest(check='entry order'):
            self.assertEqual(entries[0].findtext('atom:title', namespaces=ns), first_title)
            self.assertEqual(entries[0].findtext('atom:id', namespaces=ns), first_url)

        for entry in entries:
            book_url = entry.findtext('atom:id', namespaces=ns)
            with self.subTest(book_url=book_url):
                self.assertEqual(entry.find('atom:link', ns).get('href'), book_url)
                content = entry.find('atom:content', ns)
                self.assertEqual(content.get('type'), 'xhtml')
                cover = content.find('.//xhtml:div[@class="bookcover"]/xhtml:img', ns)
                product_id = book_url.rsplit('/', 1)[1]
                cover_url = urlsplit(cover.get('src'))
                self.assertEqual((cover_url.scheme, cover_url.netloc, cover_url.path), ('https', 'wsrv.nl', '/'))
                self.assertEqual(parse_qs(cover_url.query), {
                    'url': [f'https://taiwan-image.bookwalker.com.tw/product/{product_id}/{product_id}.jpg'],
                })
                self.assertNotIn('data-src', cover.attrib)
                self.assertNotIn('style', cover.attrib)
                for img in content.findall('.//xhtml:img', ns):
                    self.assertRegex(img.get('src'), r'^https://')

    @requests_mock.mock()
    def test_bookwalker_lightnovel(self, m):
        text = Path(__file__).with_name('html_bookwalker_lightnovel.txt').read_text(encoding='utf-8')
        m.get('https://www.bookwalker.com.tw/block/5?order=sell_desc', text=text)

        c = Client()
        res = c.get('/bookwalker-lightnovel')
        self.assertEqual(res.status_code, 200)
        self.assert_bookwalker_entries(res, '堤亞穆帝國物語(07)', 'https://www.bookwalker.com.tw/product/152448')

    @requests_mock.mock()
    def test_bookwalker_manga(self, m):
        text = Path(__file__).with_name('html_bookwalker_manga.txt').read_text(encoding='utf-8')
        m.get('https://www.bookwalker.com.tw/block/3?order=sell_desc', text=text)

        c = Client()
        res = c.get('/bookwalker-manga')
        self.assertEqual(res.status_code, 200)
        self.assert_bookwalker_entries(res, '【套書】異世界悠閒農家（漫畫）1-10（共10冊）', 'https://www.bookwalker.com.tw/product/187306')

    @requests_mock.mock()
    def test_cakeresume(self, m):
        text = Path(__file__).with_name('html_cakeresume.txt').read_text(encoding='utf-8')
        m.get('https://www.cakeresume.com/jobs/test?location_list%5B0%5D=Taiwan&order=latest', text=text)

        c = Client()
        res = c.get('/cakeresume/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_dcard_board(self, m):
        text = Path(__file__).with_name('html_dcard_board.txt').read_text(encoding='utf-8')
        m.get('https://www.dcard.tw/f/moon', text=text)

        c = Client()
        res = c.get('/dcard/board/moon')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_dcard_main(self, m):
        m.get('https://www.dcard.tw/service/api/v2/popularForums/GetHead?listKey=popularForums', text='{"listKey":"popularForums","head":"00000000-0000-0000-0000-000000000000"}')

        text = Path(__file__).with_name('json_dcard_popular.txt').read_text(encoding='utf-8')
        m.get('https://www.dcard.tw/service/api/v2/popularForums/GetPage?pageKey=00000000-0000-0000-0000-000000000000', text=text)

        c = Client()
        res = c.get('/dcard/main')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_job104(self, m):
        text = Path(__file__).with_name('json_job104.txt').read_text(encoding='utf-8')
        m.get(re.compile(r'^https://www\.104\.com\.tw/jobs/search/api/jobs'), text=text)

        c = Client()
        res = c.get('/104/test')
        self.assertEqual(res.status_code, 200)

        res = c.get('/104company/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_job1111(self, m):
        text = Path(__file__).with_name('html_job1111.txt').read_text(encoding='utf-8')
        m.get('https://www.1111.com.tw/search/job?col=da&ks=test&page=1&sort=desc', text=text)

        c = Client()
        res = c.get('/1111/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_job518(self, m):
        text = Path(__file__).with_name('html_job518.txt').read_text(encoding='utf-8')
        m.get('https://www.518.com.tw/job-index-P-1.html?i=1&am=1&ad=test&orderType=1&orderField=8', text=text)

        c = Client()
        res = c.get('/518/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_meetjobs(self, m):
        text = Path(__file__).with_name('json_meetjobs.txt').read_text(encoding='utf-8')
        m.get('https://api.meet.jobs/api/v1/jobs?page=1&order=update&q=test&include=required_skills&external_job=true', text=text)

        c = Client()
        res = c.get('/meetjobs/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_momoshop(self, m):
        m.get('https://www.momoshop.com.tw/', text='')

        text = Path(__file__).with_name('json_momoshop.txt').read_text(encoding='utf-8')
        m.post('https://www.momoshop.com.tw/ajax/ajaxTool.jsp?n=2018', text=text)

        c = Client()
        res = c.get('/momoshop/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_pchome(self, m):
        text = Path(__file__).with_name('json_pchome.txt').read_text(encoding='utf-8')
        m.get('https://ecshweb.pchome.com.tw/search/v3.3/all/results?q=test&page=1&sort=new/dc', text=text)

        c = Client()
        res = c.get('/pchome/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_pchome_lightnovel(self, m):
        text = Path(__file__).with_name('json_pchome_lightnovel.txt').read_text(encoding='utf-8')
        m.get('https://ecapi.pchome.com.tw/cdn/ecshop/prodapi/v2/newarrival/DJAZ/prod&offset=1&limit=20&fields=Id,Nick,Pic,Price,Discount,isSpec,Name,isCarrier,isSnapUp,isBigCart&_callback=jsonp_prodlist?_callback=jsonp_prodlist', text=text)

        c = Client()
        res = c.get('/pchome-lightnovel')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_plurk_search(self, m):
        text = Path(__file__).with_name('json_plurk_search.txt').read_text(encoding='utf-8')
        m.post('https://www.plurk.com/Search/search2', text=text)

        c = Client()
        res = c.get('/plurk/search/test')
        self.assertEqual(res.status_code, 200)
        self.assert_plurk_images(res)

    @requests_mock.mock()
    def test_plurk_top(self, m):
        text = Path(__file__).with_name('json_plurk_top_zh.txt').read_text(encoding='utf-8')
        m.get('https://www.plurk.com/Stats/topReplurks?period=day&lang=zh&limit=10', text=text)

        c = Client()
        res = c.get('/plurk/top/zh')
        self.assertEqual(res.status_code, 200)
        self.assert_plurk_images(res)

    @requests_mock.mock()
    def test_rent591(self, m):
        text = Path(__file__).with_name('html_rent591.txt').read_text(encoding='utf-8')
        m.get('https://rent.591.com.tw/?kind=0&order=posttime&orderType=desc&region=1&keywords=abc', text=text)

        c = Client()
        res = c.get('/rent591/1/abc')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_shopee(self, m):
        text = Path(__file__).with_name('json_shopee.txt').read_text(encoding='utf-8')
        m.get('https://shopee.tw/api/v4/search/search_items/?by=ctime&keyword=test&limit=60&newest=0&order=desc&page_type=search&scenario=PAGE_GLOBAL_SEARCH&version=2', text=text)

        c = Client()
        res = c.get('/shopee/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_taipeimetrotimetable(self, m):
        text = Path(__file__).with_name('html_taipeimetrotimetable.txt').read_text(encoding='utf-8')
        url = 'https://web.metro.taipei/img/ALL/timetables/079a.PDF'
        m.get(url, headers={'last-modified': 'Fri, 11 Nov 2022 16:20:50 GMT'}, text=text)

        c = Client()
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        for time_zone in ('UTC', 'Asia/Taipei'):
            with self.subTest(time_zone=time_zone), self.settings(TIME_ZONE=time_zone):
                res = c.get('/taipeimetrotimetable/079a')
                self.assertEqual(res.status_code, 200)
                feed = lxml.etree.fromstring(res.content)
                entries = feed.findall('atom:entry', ns)
                self.assertEqual(len(entries), 1)
                self.assertEqual(entries[0].findtext('atom:id', namespaces=ns), f'{url}?v=1668183650')
                self.assertEqual(entries[0].findtext('atom:updated', namespaces=ns), '2022-11-11T16:20:50+00:00')

    @requests_mock.mock()
    def test_yourator(self, m):
        text = Path(__file__).with_name('json_yourator.txt').read_text(encoding='utf-8')
        m.get('https://www.yourator.co/api/v2/jobs?term[]=test', text=text)

        c = Client()
        res = c.get('/yourator/test')
        self.assertEqual(res.status_code, 200)

    @requests_mock.mock()
    def test_youtube(self, m):
        text = Path(__file__).with_name('html_youtube.txt').read_text(encoding='utf-8')
        m.get('https://www.youtube.com/results?search_query=test&sp=CAESAggD&hl=en', text=text)
        m.get(re.compile(r'^https://www\.youtube\.com/watch\?v='), text='')

        c = Client()
        res = c.get('/youtube/test')
        self.assertEqual(res.status_code, 200)
