from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import html
import json
import time

from .. import services

class Job104CompanyView(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = 'https://www.104.com.tw/jobs/search/api/jobs?jobsource=index_s&keyword={}&mode=s&order=15&page=1&pagesize=20&searchJobs=1&_t='.format(keyword, time.time())

        title = '104 公司搜尋 - {}'.format(keyword)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            s = services.RequestsService().process()

            r = s.get(url, headers={'Referer': 'https://www.104.com.tw/'})
            items = json.loads(r.text)['data']
        except:
            items = []

        for item in items:
            try:
                job_desc = item['description']
                job_title = item['jobName']

                if keyword.lower() not in job_title.lower() and keyword.lower() not in job_desc.lower():
                    continue

                job_company = item['custName']
                job_company_url = item['link']['cust']

                content = '<h3>{}</h3>'.format(
                    html.escape(job_company),
                )

                entry = feed.add_entry()
                entry.author({'name': job_company})
                entry.content(content, type='xhtml')
                entry.id(job_company_url)
                entry.link(href=job_company_url)
                entry.title(job_company)
            except:
                pass

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res

class Job104View(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = 'https://www.104.com.tw/jobs/search/api/jobs?jobsource=index_s&keyword={}&mode=s&order=15&page=1&pagesize=20&searchJobs=1&_t='.format(keyword, time.time())

        title = '104 搜尋 - {}'.format(keyword)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            s = services.RequestsService().process()

            r = s.get(url, headers={'Referer': 'https://www.104.com.tw/'})
            items = json.loads(r.text)['data']
        except:
            items = []

        for item in items:
            try:
                job_desc = item['description']
                job_title = item['jobName']

                if keyword.lower() not in job_title.lower() and keyword.lower() not in job_desc.lower():
                    continue

                job_company = item['custName']
                job_url = item['link']['job']

                content = '<h3>{}</h3><pre>{}</pre>'.format(
                    html.escape(job_company),
                    html.escape(job_desc)
                )

                entry = feed.add_entry()
                entry.author({'name': job_company})
                entry.content(content, type='xhtml')
                entry.id(job_url)
                entry.link(href=job_url)
                entry.title(job_title)
            except:
                pass

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
