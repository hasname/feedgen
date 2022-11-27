from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import datetime
import html
import json
import re
import urllib

from .. import services

class CakeResumeView(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = 'https://www.cakeresume.com/jobs?q={}'.format(urllib.parse.quote_plus(keyword))

        title = 'CakeResume 搜尋 - {}'.format(keyword)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            s = services.RequestsService().process()

            r = s.get(url)
            state = re.search(r'<script>window\.__APP_INITIAL_REDUX_STATE__ = (.*?)</script>', r.text, re.MULTILINE).group(1)
            state = state.replace('"jwt":undefined', '"jwt":false')
            items = json.loads(state)['jobSearch']['jobResultsState']['content']['_rawResults'][0]['hits']
        except:
            items = []

        for item in items:
            item_author = item['page']['name']
            item_content = '<p>{}</p><p>{}</p>'.format(html.escape(item.get('requirements_plain_text', '')), html.escape(item.get('description_plain_text', '')))
            item_title = item['title']
            item_url = 'https://www.cakeresume.com/companies/{}/jobs/{}'.format(item['page']['path'], item['path'])
            item_updated_at = datetime.datetime.fromtimestamp(item['content_updated_at'] / 1000, tz=datetime.timezone.utc)

            entry = feed.add_entry()
            entry.author({'name': item_author})
            entry.content(item_content, type='xhtml')
            entry.id(item_url)
            entry.link(href=item_url)
            entry.title(item_title)
            entry.updated(item_updated_at)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
