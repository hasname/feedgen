from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import html
import json
import re
import urllib

from .. import services

class PChomeLightNovelView(View):
    def get(self, *args, **kwargs):
        url = 'https://ecapi.pchome.com.tw/cdn/ecshop/prodapi/v2/newarrival/DJAZ/prod&offset=1&limit=20&fields=Id,Nick,Pic,Price,Discount,isSpec,Name,isCarrier,isSnapUp,isBigCart&_callback=jsonp_prodlist?_callback=jsonp_prodlist'

        title = 'PChome 輕小說'

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            s = services.RequestsService().process()

            r = s.get(url)
            body = re.match(r'^[^\[]*(\[.*\])[^\[]*$', r.text).group(1)
            items = json.loads(body)
        except:
            items = []

        for item in items:
            content = '{}<br/><img alt="{}" src="https://cs-a.ecimg.tw{}"/>'.format(
                html.escape(item['Nick']),
                html.escape(item['Nick']),
                html.escape(item['Pic']['B']),
            )
            book_title = item['Nick']
            book_url = 'https://24h.pchome.com.tw/books/prod/{}'.format(
                urllib.parse.quote_plus(item['Id'])
            )

            entry = feed.add_entry()
            entry.content(content, type='xhtml')
            entry.id(book_url)
            entry.title(book_title)
            entry.link(href=book_url)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res

class PChomeView(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = 'https://ecshweb.pchome.com.tw/search/v3.3/all/results?q={}&page=1&sort=new/dc'.format(urllib.parse.quote_plus(keyword))

        title = 'PChome 搜尋 - {}'.format(keyword)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            s = services.RequestsService().process()

            r = s.get(url)
            body = json.loads(r.text)
        except:
            body = {'prods': []}

        for item in body['prods']:
            # Product name & description
            item_author = self.str_clean(item['author'])
            item_desc = self.str_clean(item['describe'])
            item_name = self.str_clean(item['name'])
            item_origin_price = item['originPrice']
            item_price = item['price']
            item_title = '(${}/${}) {}'.format(item_origin_price, item_price, item_name)

            # URL
            if item['cateId'][0] == 'D':
                item_url = 'https://24h.pchome.com.tw/prod/' + item['Id']
            else:
                item_url = 'https://mall.pchome.com.tw/prod/' + item['Id']
            img_url = 'https://cs-a.ecimg.tw%s' % (item['picB'])

            content = '{}<br/><img alt="{}" src="{}"/>'.format(
                html.escape(item_desc), html.escape(item_name), html.escape(img_url)
            )

            entry = feed.add_entry()
            entry.author({'name': item_author})
            entry.content(content, type='xhtml')
            entry.id(item_url)
            entry.link(href=item_url)
            entry.title(item_title)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res

    def str_clean(self, s):
        return re.sub(r'[\x00-\x09]', ' ', s)
