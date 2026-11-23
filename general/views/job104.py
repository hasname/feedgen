import html
import logging
from urllib.parse import quote_plus, urljoin

import feedgen.feed
from django.http import HttpResponse
from django.views.generic import View
from requests.exceptions import RequestException

from .. import services

logger = logging.getLogger(__name__)


class Job104View(View):
    company = False

    def get(self, request, keyword):
        url = f'https://www.104.com.tw/jobs/search/api/jobs?jobsource=index_s&keyword={quote_plus(keyword)}&mode=s&order=16&page=1&pagesize=20&searchJobs=1'
        try:
            with services.CurlCffiService().process('104') as session:
                response = session.get(url, headers={'Referer': 'https://www.104.com.tw/', 'Sec-Fetch-Mode': 'cors'})
                response.raise_for_status()
                items = response.json()['data']
            if not isinstance(items, list):
                raise TypeError('Expected a list of 104 jobs')
        except (RequestException, KeyError, TypeError, ValueError):
            logger.exception('Failed to fetch or parse 104 search results')
            return HttpResponse(
                '無法取得 104 搜尋結果。', status=502, content_type='text/plain; charset=utf-8',
                headers={'Cache-Control': 'no-store'},
            )

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=f'https://www.104.com.tw/jobs/search/?keyword={quote_plus(keyword)}', rel='alternate')
        feed.title(f'104 公司搜尋 - {keyword}' if self.company else f'104 搜尋 - {keyword}')

        term = keyword.lower()
        for item in items:
            try:
                job_title = item['jobName']
                job_desc = item['description']
                if term not in job_title.lower() and term not in job_desc.lower():
                    continue

                company = item['custName']
                link = item['link']['cust' if self.company else 'job']
                if not link:
                    continue
                link = urljoin('https://www.104.com.tw/', link)
                content = f'<h3>{html.escape(company)}</h3>'
                if not self.company:
                    content += f'<pre>{html.escape(job_desc)}</pre>'

                entry = feed.add_entry()
                entry.author({'name': company})
                entry.content(content, type='xhtml')
                entry.id(link)
                entry.link(href=link)
                entry.title(company if self.company else job_title)
            except (AttributeError, KeyError, TypeError, ValueError):
                logger.exception('Failed to generate 104 entry')

        return HttpResponse(
            feed.atom_str(), content_type='application/atom+xml; charset=utf-8',
            headers={'Cache-Control': 'max-age=300,public'},
        )


class Job104CompanyView(Job104View):
    company = True
