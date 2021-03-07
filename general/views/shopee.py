from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import html
import json
import requests
import urllib

class ShopeeView(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = 'https://shopee.tw/api/v2/search_items/?by=ctime&keyword={}&limit=50&newest=0&order=desc&page_type=search&version=2'.format(urllib.parse.quote_plus(keyword))
        referer = 'https://shopee.tw/search?keyword={}'.format(urllib.parse.quote_plus(keyword))

        title = '蝦皮搜尋 - {}'.format(keyword)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            s = requests.Session()
            r = s.get(url, headers={'Referer': referer, 'User-agent': 'feedgen'}, timeout=5)
            body = json.loads(r.text)
            items = body['items']
        except:
            items = []

        if not isinstance(items, list):
            items = []

        for item in items:
            itemid = item['itemid']
            name = item['name']
            shopid = item['shopid']

            prod_url = 'https://shopee.tw/product/%d/%d' % (shopid, itemid)
            img_url = 'https://cf.shopee.tw/file/%s' % (item['image'])

            content = '{}<br/><img alt="{}" src="{}"/>'.format(
                html.escape(name), html.escape(name), html.escape(img_url)
            )

            entry = feed.add_entry()
            entry.content(content, type='xhtml')
            entry.id(prod_url)
            entry.link(href=prod_url)
            entry.title(name)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml')
        res['Cache-Control'] = 'max-age=300,public'

        return res
