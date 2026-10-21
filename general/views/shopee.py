import html
import json
import urllib

import feedgen.feed
from django.http import HttpResponse
from django.views.generic import View

from .. import services


class ShopeeView(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = f'https://shopee.tw/api/v4/search/search_items/?by=ctime&keyword={urllib.parse.quote_plus(keyword)}&limit=60&newest=0&order=desc&page_type=search&scenario=PAGE_GLOBAL_SEARCH&version=2'
        referer = f'https://shopee.tw/search?keyword={urllib.parse.quote_plus(keyword)}'

        title = f'蝦皮搜尋 - {keyword}'

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        s = services.RequestsService().process('shopee')

        r = s.get(url, headers={'Referer': referer})
        body = json.loads(r.text)
        items = body['items']

        if not isinstance(items, list):
            items = []

        for item in items:
            itemid = item['itemid']
            item_basic = item['item_basic']

            name = item_basic['name']
            shopid = item_basic['shopid']

            prod_url = f'https://shopee.tw/product/{shopid:d}/{itemid:d}'
            img_url = f'https://cf.shopee.tw/file/{item_basic["image"]}'

            content = f'{html.escape(name)}<br/><img alt="{html.escape(name)}" src="{html.escape(img_url)}"/>'

            entry = feed.add_entry()
            entry.content(content, type='xhtml')
            entry.id(prod_url)
            entry.link(href=prod_url)
            entry.title(name)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
