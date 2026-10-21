import html
import urllib

import feedgen.feed
import lxml.html
from django.http import HttpResponse
from django.views.generic import View

from .. import services


class Job1111View(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = f'https://www.1111.com.tw/search/job?col=da&ks={urllib.parse.quote_plus(keyword)}&page=1&sort=desc'

        title = f'1111 搜尋 - {keyword}'

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        s = services.RequestsService().process('1111')

        r = s.get(url)
        r.encoding = 'utf-8'
        body = lxml.html.fromstring(r.text)

        for item in body.cssselect('div.job_item'):
            a = item.cssselect('.job_item_info a')[0]
            job_title = a.text_content()
            job_url = a.get('href')
            if job_url.startswith('/job/'):
                job_url = 'https://www.1111.com.tw' + job_url

            job_company = item.cssselect('div.card-subtitle a')[0].get('title')

            job_desc = item.cssselect('p.job_item_description')[0].text_content()
            content = f'<h3>{html.escape(job_company)}</h3><p>{html.escape(job_desc)}</p>'

            entry = feed.add_entry()
            entry.content(content, type='xhtml')
            entry.id(job_url)
            entry.link(href=job_url)
            entry.title(job_title)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
