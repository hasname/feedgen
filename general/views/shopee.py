from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import html
import json
import urllib

from .. import services

class ShopeeView(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = 'https://shopee.tw/api/v4/search/search_items/?by=ctime&keyword={}&limit=60&newest=0&order=desc&page_type=search&scenario=PAGE_GLOBAL_SEARCH&version=2'.format(urllib.parse.quote_plus(keyword))
        referer = 'https://shopee.tw/search?keyword={}'.format(urllib.parse.quote_plus(keyword))

        title = '蝦皮搜尋 - {}'.format(keyword)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            proxy = services.ProxySocks5Service().process()
            s = services.RequestsService().process()
            s.proxies = {'http': proxy, 'https': proxy}

            r = s.get(url, headers={'Referer': referer})
            body = json.loads(r.text)
            items = body['items']
        except:
            return HttpResponse('Service Unavailable', status=503)

        if not isinstance(items, list):
            items = []

        for item in items:
            itemid = item['itemid']
            item_basic = item['item_basic']

            name = item_basic['name']
            shopid = item_basic['shopid']

            prod_url = 'https://shopee.tw/product/%d/%d' % (shopid, itemid)
            img_url = 'https://cf.shopee.tw/file/%s' % (item_basic['image'])

            content = '{}<br/><img alt="{}" src="{}"/>'.format(
                html.escape(name), html.escape(name), html.escape(img_url)
            )

            entry = feed.add_entry()
            entry.content(content, type='xhtml')
            entry.id(prod_url)
            entry.link(href=prod_url)
            entry.title(name)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
