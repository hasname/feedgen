from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import datetime
import html
import json
import re
import urllib

from .. import services

class YouratorView(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = 'https://www.yourator.co/api/v2/jobs?term[]={}'.format(urllib.parse.quote_plus(keyword))

        title = 'Yourator 搜尋 - {}'.format(keyword)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            s = services.RequestsService().process()

            r = s.get(url)
            items = r.json()['jobs']
        except:
            items = []

        for item in items:
            job_city = item['city']
            job_company = item['company']['brand']
            job_link = 'https://www.yourator.co' + item['path']
            job_salary = item['salary']
            job_title = item['name']

            item_author = job_company
            item_content = '<h3>{}</h3><p>{} {}</p>'.format(html.escape(job_company), html.escape(job_city), html.escape(job_salary))
            item_title = job_title
            item_url = job_link

            entry = feed.add_entry()
            entry.author({'name': item_author})
            entry.content(item_content, type='xhtml')
            entry.id(item_url)
            entry.link(href=item_url)
            entry.title(item_title)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
