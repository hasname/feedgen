from django.http import HttpResponse
from django.views.generic import View
import base36
import dateutil.parser
import feedgen.feed
import json
import re
import urllib

from .. import services

class PlurkSearchView(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = 'https://www.plurk.com/Search/search2'

        title = 'Plurk Search - {}'.format(keyword)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        s = services.RequestsService().process()

        r = s.post(url, data={'query': keyword})
        body = json.loads(r.text)

        users = body['users']

        for p in body['plurks']:
            url = 'https://www.plurk.com/p/' + base36.dumps(p['id'])

            author = users[str(p['owner_id'])]['nick_name']
            content = self.str_clean(p['content'])

            entry = feed.add_entry()
            entry.author(name=author)
            entry.content(content, type='CDATA')
            entry.id(url)
            entry.link(href=url)
            entry.published(dateutil.parser.parse(p['posted']))
            entry.title(self.str_clean(p['content_raw']) or 'None')

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res

    def str_clean(self, s):
        return re.sub(r'[\x00-\x09]', ' ', s)

class PlurkTopView(View):
    def get(self, *args, **kwargs):
        lang = kwargs['lang']

        url = 'https://www.plurk.com/Stats/topReplurks?period=day&lang={}&limit=10'.format(urllib.parse.quote_plus(lang))

        title = 'Plurk Top ({})'.format(lang)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        s = services.RequestsService().process()

        r = s.get(url)
        body = json.loads(r.text)

        for (x, stat) in body['stats']:
            url = 'https://www.plurk.com/p/' + base36.dumps(stat['id'])

            content = self.str_clean(stat['content'])
            content = re.sub(r' height="\d+(px)?"', ' ', content)
            content = re.sub(r' width="\d+(px)?"', ' ', content)

            entry = feed.add_entry()
            entry.author({'name': self.str_clean(stat['owner']['full_name'])})
            entry.content(content, type='CDATA')
            entry.id(url)
            entry.link(href=url)
            entry.published(stat['posted'])
            entry.title(self.str_clean(stat['content_raw']))

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res

    def str_clean(self, s):
        return re.sub(r'[\x00-\x09]', ' ', s)
