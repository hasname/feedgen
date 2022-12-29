from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import datetime
import html
import json
import re
import urllib

from .. import services

class MeetJobsView(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = 'https://meet.jobs/zh-TW/jobs?page=1&order=update&q={}'.format(urllib.parse.quote_plus(keyword))
        api_url = 'https://api.meet.jobs/api/v1/jobs?page=1&order=update&q={}&include=required_skills&external_job=true'.format(urllib.parse.quote_plus(keyword))

        title = 'meet.jobs 搜尋 - {}'.format(keyword)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            s = services.RequestsService().process()

            r = s.get(api_url)
            items = r.json()['collection']
        except:
            items = []

        for item in items:
            job_company = item['employer']['name']
            job_desc = item['description']
            job_features = item['work_type']
            job_link = 'https://meet.jobs/zh-TW/jobs/{}-{}'.format(item['id'], item['slug'])
            job_published_at = item['published_at']
            job_title = item['title']
            job_updated_at = item['updated_at']

            item_author = job_company
            item_content = '<p>{}</p><p>{}</p>'.format(html.escape(job_features), html.escape(job_desc))
            item_title = job_title
            item_url = job_link

            entry = feed.add_entry()
            entry.author({'name': item_author})
            entry.content(item_content, type='xhtml')
            entry.id(item_url)
            entry.link(href=item_url)
            entry.published(datetime.datetime.strptime(item['published_at'], '%Y-%m-%dT%H:%M:%S.%f%z'))
            entry.title(item_title)
            entry.updated(datetime.datetime.strptime(item['updated_at'], '%Y-%m-%dT%H:%M:%S.%f%z'))

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
