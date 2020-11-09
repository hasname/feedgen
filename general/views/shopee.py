from concurrent.futures import ThreadPoolExecutor
from django.http import HttpResponse
from django.views.generic import View
from requests_futures.sessions import FuturesSession
import feedgen.feed
import html
import json
import requests
import urllib

class ShopeeView(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = 'https://shopee.tw/api/v2/search_items/?by=ctime&keyword={}&limit=50&newest=0&order=desc&page_type=search'.format(urllib.parse.quote_plus(keyword))
        referer = 'https://shopee.tw/search?keyword={}'.format(urllib.parse.quote_plus(keyword))

        title = '蝦皮搜尋 - {}'.format(keyword)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        s = requests.Session()
        r = s.get(url, headers={'Referer': referer, 'User-agent': 'feedgen'}, timeout=5)

        try:
            body = json.loads(r.text)
        except json.decoder.JSONDecodeError:
            body = {'items': []}

        session = FuturesSession(executor=ThreadPoolExecutor(max_workers=8))
        futures = []

        for item in body['items']:
            shopid = item['shopid']
            shopapi_url = 'https://shopee.tw/api/v2/shop/get?is_brief=1&shopid=%d' % shopid
            futures.append(
                session.get(shopapi_url, headers={'Referer': referer, 'User-agent': 'feedgen'}, timeout=5)
            )

        shops = {}
        for f in futures:
            r = f.result()
            try:
                data = json.loads(r.text)['data']
            except json.decoder.JSONDecodeError:
                continue

            shopid = data['shopid']
            username = data['account']['username']

            shops[shopid] = username

        session = FuturesSession(executor=ThreadPoolExecutor(max_workers=8))
        futures = []

        for item in body['items']:
            itemid = item['itemid']
            name = item['name']
            shopid = item['shopid']

            itemapi_url = 'https://shopee.tw/api/v2/item/get?itemid=%d&shopid=%d' % (
                itemid,
                shopid,
            )
            futures.append(
                session.get(itemapi_url, headers={'User-agent': 'feedgen'}, timeout=5)
            )

        for f in futures:
            r = f.result()
            try:
                item = json.loads(r.text)['item']
            except json.decoder.JSONDecodeError:
                continue

            itemid = item['itemid']
            name = item['name']
            shopid = item['shopid']

            prod_url = 'https://shopee.tw/product/%d/%d' % (shopid, itemid)
            img_url = 'https://cf.shopee.tw/file/%s' % (item['image'])

            content = '{}<br/><img alt="{}" src="{}"/>'.format(
                html.escape(name), html.escape(name), html.escape(img_url)
            )

            entry = feed.add_entry()
            entry.author({'name': shops.get(shopid, None)})
            entry.content(content, type='xhtml')
            entry.id(prod_url)
            entry.link(href=prod_url)
            entry.title(name)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml')
        res['Cache-Control'] = 'max-age=300,public'

        return res
