import html
import logging
import re
import urllib

import feedgen.feed
import lxml.html
from django.http import HttpResponse
from django.views.generic import View

from .. import services

logger = logging.getLogger(__name__)


class Job518View(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = f'https://www.518.com.tw/job-index-P-1.html?i=1&am=1&ad={urllib.parse.quote_plus(keyword)}&orderType=1&orderField=8'

        title = f'518 搜尋 - {keyword}'

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            s = services.RequestsService().process()

            r = s.get(url)
            body = lxml.html.fromstring(r.text)
        except Exception:
            logger.exception('Failed to fetch or parse 518 search results')
            body = lxml.html.fromstring('<html></html>')

        for item in body.cssselect('#listContent > ul'):
            try:
                a = item.cssselect('li.title a')[0]
                job_title = a.getchildren()[0].text_content()

                job_url = a.get('href')
                job_url = re.sub('\\?.*', '', job_url)

                job_company = item.cssselect('li.company')[0].text_content()

                job_desc = item.cssselect('li.sumbox')[0].text_content()
                content = f'<h3>{html.escape(job_company)}</h3><p>{html.escape(job_desc)}</p>'

                entry = feed.add_entry()
                entry.content(content, type='xhtml')
                entry.id(job_url)
                entry.link(href=job_url)
                entry.title(job_title)

            except IndexError:
                pass

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
