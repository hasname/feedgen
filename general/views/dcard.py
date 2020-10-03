from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import html
import lxml.html
import requests
import urllib

class DcardMainView(View):
    def get(self, *args, **kwargs):
        url = 'https://www.dcard.tw/f'

        title = 'Dcard 首頁'

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        s = requests.Session()
        r = s.get(url, headers={'User-agent': 'feedgen'}, timeout=5)
        body = lxml.html.fromstring(r.text)

        items = body.cssselect('div[data-index] > article[role="article"]')
        for item in items:
            item_title = item.cssselect('h2')[0].text_content()
            item_url = item.cssselect('h2 > a')[0].get('href')
            item_desc = item.cssselect('h2 + div')[0].text_content()
            item_img = item.cssselect('img')[0].get('src')

            if item_url.startswith('/f/'):
                item_url = 'https://www.dcard.tw' + item_url

            if item_img is None:
                item_content = '{}'.format(
                    html.escape(item_desc)
                )
            else:
                item_content = '<img alt="{}" src="{}"/><br/>{}'.format(
                    html.escape(item_title),
                    html.escape(item_img),
                    html.escape(item_desc)
                )

            entry = feed.add_entry()
            entry.content(item_content, type='xhtml')
            entry.id(item_url)
            entry.title(item_title)
            entry.link(href=item_url)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml')
        res['Cache-Control'] = 'max-age=300,public'

        return res
