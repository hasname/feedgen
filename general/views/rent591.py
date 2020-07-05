from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import html
import lxml.html
import re
import requests

class Rent591View(View):
    def get(self, *args, **kwargs):
        region = kwargs['region']
        keyword = kwargs['keyword']

        url = 'https://rent.591.com.tw/?kind=0&order=posttime&orderType=desc&region={}&keywords={}'.format(region, keyword)

        title = '591 出租搜尋 - {}'.format(keyword)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        s = requests.Session()
        r = s.get(url, headers={'User-agent': 'feedgen'}, timeout=5)
        body = lxml.html.fromstring(r.text)

        for item in body.cssselect('#content > ul'):
            item_desc = item.text_content()
            item_title = item.cssselect('.infoContent')[0].text_content()
            item_url = item.cssselect('a')[0].get('href')
            item_url = re.sub(r'^//', 'https://', item_url)

            content = '{}<br/>{}'.format(
                html.escape(item_title), html.escape(item_desc)
            )

            entry = feed.add_entry()
            entry.content(content, type='xhtml')
            entry.id(item_url)
            entry.link(href=item_url)
            entry.title(item_title)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml')
        res['Cache-Control'] = 'max-age=300,public'

        return res
