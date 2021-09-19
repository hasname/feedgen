from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import html
import lxml.html
import re
import requests
import urllib

from .. import services

class Job1111View(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = 'https://www.1111.com.tw/search/job?flag=13&ks={}&fs=1&si=1&ts=4&col=da&sort=desc'.format(urllib.parse.quote_plus(keyword))

        title = '1111 搜尋 - {}'.format(keyword)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        s = services.RequestsService().process()

        r = s.get(url)
        r.encoding = 'utf-8'
        body = lxml.html.fromstring(r.text)

        for item in body.cssselect('li.jbInfo'):
            a = item.cssselect('a.mobileItemClick')[0]
            job_title = a.get('title')
            job_url = a.get('href')
            if job_url.startswith('/job/'):
                job_url = 'https://www.1111.com.tw' + job_url

            job_company = item.cssselect('a.d-block.organ')[0].get('title')

            job_desc = item.cssselect('.jbInfoTxt')[0].text_content()
            content = '<h3>{}</h3><p>{}</p>'.format(
                html.escape(job_company), html.escape(job_desc)
            )

            entry = feed.add_entry()
            entry.content(content, type='xhtml')
            entry.id(job_url)
            entry.link(href=job_url)
            entry.title(job_title)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
