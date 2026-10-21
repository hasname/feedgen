import re
from urllib.parse import urlencode

import feedgen.feed
import lxml.html
from django.http import HttpResponse
from django.views.generic import View

from .. import services


class BookwalkerMangaView(View):
    def get(self, *args, **kwargs):
        url = 'https://www.bookwalker.com.tw/block/3?order=sell_desc'

        title = 'BOOKWALKER 漫畫'

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        s = services.RequestsService().process('bookwalker')

        r = s.get(url)
        body = lxml.html.fromstring(r.text)

        for item in body.cssselect('.bookitem a'):
            img = item.cssselect('img')[0]
            img_src = img.get('data-src')
            img_src = re.sub(r'_4(_mask)?\.jpg$', '.jpg', img_src)
            img.set('src', img_src)
            del img.attrib['data-src']
            img.attrib.pop('style', None)
            item.make_links_absolute(url)
            img.set('src', 'https://wsrv.nl/?' + urlencode({'url': img.get('src')}))

            content = lxml.etree.tostring(item, encoding='unicode')
            book_title = item.get('title')
            book_url = item.get('href')

            entry = feed.add_entry(order='append')
            entry.content(content, type='xhtml')
            entry.id(book_url)
            entry.title(book_title)
            entry.link(href=book_url)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res

class BookwalkerLightNovelView(View):
    def get(self, *args, **kwargs):
        url = 'https://www.bookwalker.com.tw/block/5?order=sell_desc'

        title = 'BOOKWALKER 輕小說'

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        s = services.RequestsService().process('bookwalker')

        r = s.get(url)
        body = lxml.html.fromstring(r.text)

        for item in body.cssselect('.bookitem a'):
            img = item.cssselect('img')[0]
            img_src = img.get('data-src')
            img_src = re.sub(r'_4(_mask)?\.jpg$', '.jpg', img_src)
            img.set('src', img_src)
            del img.attrib['data-src']
            img.attrib.pop('style', None)
            item.make_links_absolute(url)
            img.set('src', 'https://wsrv.nl/?' + urlencode({'url': img.get('src')}))

            content = lxml.etree.tostring(item, encoding='unicode')
            book_title = item.get('title')
            book_url = item.get('href')

            entry = feed.add_entry(order='append')
            entry.content(content, type='xhtml')
            entry.id(book_url)
            entry.title(book_title)
            entry.link(href=book_url)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
