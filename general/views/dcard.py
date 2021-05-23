from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import html
import json
import lxml.html
import re
import requests
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
            proxy = services.ProxyService().process()

            s = requests.Session()
            s.proxies = {'http': proxy, 'https': proxy}
            r = s.get(url, headers={'User-agent': 'feedgen'}, timeout=5)
            body = lxml.html.fromstring(r.text)
        except:
            return HttpResponse('Service Unavailable', status=503)

        items = body.cssselect('div[data-index]')
        for item in items:
            if not item.cssselect('article'):
                continue

            item_title = item.cssselect('article > h2')[0].text_content()
            item_url = item.cssselect('article > h2 > a')[0].get('href')
            item_desc = item.cssselect('article > h2 + div')[0].text_content()
            try:
                item_img = item.cssselect('article > img')[0]
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

        try:
            proxy = services.ProxyService().process()

            s = requests.Session()
            s.proxies = {'http': proxy, 'https': proxy}
            r = s.get(url, headers={'User-agent': 'feedgen'}, timeout=5)
            body = lxml.html.fromstring(r.text)
        except:
            return HttpResponse('Service Unavailable', status=503)

        items = body.cssselect('div[data-index]')
        for item in items:
            if not item.cssselect('article'):
                continue

            item_title = item.cssselect('article > h2')[0].text_content()
            item_url = item.cssselect('article > h2 > a')[0].get('href')
            item_desc = item.cssselect('article > h2 + div')[0].text_content()
            try:
                item_img = item.cssselect('article > img')[0]
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
