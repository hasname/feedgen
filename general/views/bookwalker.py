from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import lxml.html
import requests

class BookwalkerLightNovelView(View):
    def get(self, *args, **kwargs):
        url = 'https://www.bookwalker.com.tw/more/fiction/1/3'

        title = 'BOOKWALKER 輕小說'

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        s = requests.Session()
        r = s.get(url, headers={'User-agent': 'feedgen'}, timeout=5)
        body = lxml.html.fromstring(r.text)

        for item in body.cssselect('.bwbookitem a'):
            img = item.cssselect('img')[0]
            img.set('src', img.get('data-src'))
            content = lxml.etree.tostring(item, encoding='unicode')
            book_title = item.get('title')
            book_url = item.get('href')

            entry = feed.add_entry()
            entry.content(content, type='xhtml')
            entry.id(book_url)
            entry.title(book_title)
            entry.link(href=book_url)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
