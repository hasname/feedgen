import html
import json
import logging

import feedgen.feed
from django.http import HttpResponse
from django.views.generic import View

from .. import services

logger = logging.getLogger(__name__)


class Job104CompanyView(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = f'https://www.104.com.tw/jobs/search/api/jobs?jobsource=index_s&keyword={keyword}&mode=s&order=16&page=1&pagesize=20&searchJobs=1'

        title = f'104 公司搜尋 - {keyword}'

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            s = services.RequestsService().process()

            r = s.get(url, headers={'Referer': 'https://www.104.com.tw/'})
            items = json.loads(r.text)['data']
        except Exception:
            logger.exception('Failed to fetch or parse 104 company search results')
            items = []

        for item in items:
            try:
                job_desc = item['description']
                job_title = item['jobName']

                if keyword.lower() not in job_title.lower() and keyword.lower() not in job_desc.lower():
                    continue

                job_company = item['custName']
                job_company_url = item['link']['cust']

                content = f'<h3>{html.escape(job_company)}</h3>'

                entry = feed.add_entry()
                entry.author({'name': job_company})
                entry.content(content, type='xhtml')
                entry.id(job_company_url)
                entry.link(href=job_company_url)
                entry.title(job_company)
            except Exception:
                logger.exception('Failed to generate 104 company entry')

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res

class Job104View(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = f'https://www.104.com.tw/jobs/search/api/jobs?jobsource=index_s&keyword={keyword}&mode=s&order=16&page=1&pagesize=20&searchJobs=1'

        title = f'104 搜尋 - {keyword}'

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            s = services.RequestsService().process()

            r = s.get(url, headers={'Referer': 'https://www.104.com.tw/'})
            items = json.loads(r.text)['data']
        except Exception:
            logger.exception('Failed to fetch or parse 104 job search results')
            items = []

        for item in items:
            try:
                job_desc = item['description']
                job_title = item['jobName']

                if keyword.lower() not in job_title.lower() and keyword.lower() not in job_desc.lower():
                    continue

                job_company = item['custName']
                job_url = item['link']['job']

                content = f'<h3>{html.escape(job_company)}</h3><pre>{html.escape(job_desc)}</pre>'

                entry = feed.add_entry()
                entry.author({'name': job_company})
                entry.content(content, type='xhtml')
                entry.id(job_url)
                entry.link(href=job_url)
                entry.title(job_title)
            except Exception:
                logger.exception('Failed to generate 104 job entry')

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
