from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import html
import json
import lxml.html
import re
import urllib

from .. import services

class DcardBoardView(View):
    def get(self, *args, **kwargs):
        board = kwargs['board']
        url = 'https://www.dcard.tw/f/{}'.format(urllib.parse.quote_plus(board))

        title = 'Dcard 看板 - {}'.format(board)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            s = services.RequestsService().process()

            r = s.get(url)
            body = lxml.html.fromstring(r.text)
        except:
            return HttpResponse('Service Unavailable', status=503)

        items = body.cssselect('div[role="main"] article')
        for item in items:
            item_title = item.cssselect('h2')[0].text_content()
            item_url = item.cssselect('h2 > a')[0].get('href')
            item_desc = item.cssselect('h2 + div')[0].text_content()
            try:
                item_img = item.cssselect('img')[0]
            except IndexError:
                item_img_src = None
            else:
                item_img_src = item_img.get('src')
                g = re.match(r'^(https://imgur\.dcard\.tw/\w+)b(\.jpg)$', item_img_src)
                if g:
                    item_img_src = g.group(1) + g.group(2)

            if item_url.startswith('/f/'):
                item_url = 'https://www.dcard.tw' + item_url

            if item_img_src is None:
                item_content = '{}'.format(
                    html.escape(item_desc)
                )
            else:
                item_content = '<img alt="{}" src="{}"/><br/>{}'.format(
                    html.escape(item_title),
                    html.escape(item_img_src),
                    html.escape(item_desc)
                )

            entry = feed.add_entry()
            entry.content(item_content, type='xhtml')
            entry.id(item_url)
            entry.title(item_title)
            entry.link(href=item_url)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res

class DcardMainView(View):
    def get(self, *args, **kwargs):
        url = 'https://www.dcard.tw/f'

        title = 'Dcard 首頁'

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        s = services.RequestsService().process()

        r = s.get('https://www.dcard.tw/service/api/v2/popularForums/GetHead?listKey=popularForums')
        if r.status_code == 200:
            head = r.json()['head']
            r = s.get('https://www.dcard.tw/service/api/v2/popularForums/GetPage?pageKey={}'.format(head))
            items = r.json()['items']
        else:
            items = []

        for item in items:
            item_title = '[{}] {}'.format(item['name'], item['posts'][0]['title'])
            item_url = 'https://www.dcard.tw/f/{}/p/{}'.format(item['alias'], item['posts'][0]['id'])
            item_desc = item['posts'][0]['excerpt']

            item_content = '<p>{}</p>'.format(
                html.escape(item_desc)
            )

            entry = feed.add_entry()
            entry.content(item_content, type='xhtml')
            entry.id(item_url)
            entry.title(item_title)
            entry.link(href=item_url)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
