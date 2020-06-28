from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import html
import json
import re
import requests
import urllib

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

        s = requests.Session()
        r = s.get(url, headers={'User-agent': 'feedgen'}, timeout=5)
        body = json.loads(r.text)

        for prod in body['prods']:
            # Product name & description
            prod_name = self.str_clean(prod['name'])
            prod_desc = self.str_clean(prod['describe'])
            prod_author = self.str_clean(prod['author'])

            # URL
            if prod['cateId'][0] == 'D':
                prod_url = 'https://24h.pchome.com.tw/prod/' + prod['Id']
            else:
                prod_url = 'https://mall.pchome.com.tw/prod/' + prod['Id']
            img_url = 'https://a.ecimg.tw%s' % (prod['picB'])

            content = '{}<br/><img alt="{}" src="{}"/>'.format(
                html.escape(prod_desc), html.escape(prod_name), html.escape(img_url)
            )

            entry = feed.add_entry()
            entry.author({'name': prod_author})
            entry.content(content, type='xhtml')
            entry.id(prod_url)
            entry.link(href=prod_url)
            entry.title(prod_name)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml')
        res['Cache-Control'] = 'max-age=300,public'

        return res

    def str_clean(self, s):
        return re.sub(r'[\x00-\x09]', ' ', s)
