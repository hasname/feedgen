import html
import logging
import re
import urllib

import feedgen.feed
import lxml.html
from django.http import HttpResponse
from django.views.generic import View

from .. import services

logger = logging.getLogger(__name__)


class DcardBoardView(View):
    def get(self, *args, **kwargs):
        board = kwargs['board']
        url = f'https://www.dcard.tw/f/{urllib.parse.quote_plus(board)}'

        title = f'Dcard 看板 - {board}'

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            s = services.RequestsService().process('dcard')

            r = s.get(url)
            body = lxml.html.fromstring(r.text)
        except Exception:
            logger.exception('Failed to fetch or parse Dcard board')
            return HttpResponse('Service Unavailable', status=503)

        items = body.cssselect('div[role="main"] article')
        for item in items:
            item_title = item.cssselect('h2')[0].text_content()
            item_url = item.cssselect('h2 > a')[0].get('href')
            item_desc = item.cssselect('h2 + div')[0].text_content()
            # Article thumbnails can be in noscript; skip placeholders and reaction icons.
            item_img_src = next((
                img.get('src') for img in item.cssselect('img[alt="thumbnail"]')
                if img.get('src', '').startswith(('https://', 'http://'))
            ), None)
            if item_img_src:
                g = re.match(r'^(https://imgur\.dcard\.tw/\w+)b(\.jpg)$', item_img_src)
                if g:
                    item_img_src = g.group(1) + g.group(2)

            if item_url.startswith('/f/'):
                item_url = 'https://www.dcard.tw' + item_url

            if item_img_src is None:
                item_content = f'{html.escape(item_desc)}'
            else:
                item_content = f'<img alt="{html.escape(item_title)}" src="{html.escape(item_img_src)}"/><br/>{html.escape(item_desc)}'

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

        s = services.RequestsService().process('dcard')

        r = s.get('https://www.dcard.tw/service/api/v2/popularForums/GetHead?listKey=popularForums')
        if r.status_code == 200:
            head = r.json()['head']
            r = s.get(f'https://www.dcard.tw/service/api/v2/popularForums/GetPage?pageKey={head}')
            items = r.json()['items']
        else:
            items = []

        for item in items:
            item_title = '[{}] {}'.format(item['name'], item['posts'][0]['title'])
            item_url = 'https://www.dcard.tw/f/{}/p/{}'.format(item['alias'], item['posts'][0]['id'])
            item_desc = item['posts'][0]['excerpt']

            item_content = f'<p>{html.escape(item_desc)}</p>'

            entry = feed.add_entry()
            entry.content(item_content, type='xhtml')
            entry.id(item_url)
            entry.title(item_title)
            entry.link(href=item_url)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
