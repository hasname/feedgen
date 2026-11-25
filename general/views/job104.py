import html
import logging
from time import sleep, time
from urllib.parse import quote_plus, urljoin

import feedgen.feed
from django.http import HttpResponse
from django.utils.http import parse_http_date_safe
from django.views.generic import View
from requests.exceptions import RequestException

from .. import services

logger = logging.getLogger(__name__)
RETRY_DELAYS = (1, 2)
RETRY_STATUS_CODES = {408, 429, 500, 502, 503, 504}
MAX_RETRY_DELAY = 5


def _retry_after(response):
    value = response.headers.get('Retry-After', '').strip()
    if value.isascii() and value.isdecimal():
        return float(value)
    if value:
        retry_at = parse_http_date_safe(value)
        if retry_at is not None:
            return retry_at - time()
    return 0


def _get_with_retry(session, url, **kwargs):
    for delay in RETRY_DELAYS:
        try:
            response = session.get(url, **kwargs)
        except RequestException:
            pass
        else:
            if response.status_code not in RETRY_STATUS_CODES:
                return response
            delay = max(delay, _retry_after(response))
            if delay > MAX_RETRY_DELAY:
                return response
        sleep(delay)
    return session.get(url, **kwargs)


class Job104View(View):
    company = False

    def get(self, request, keyword):
        base_url = 'https://www.104.com.tw/jobs/search/'
        encoded_keyword = quote_plus(keyword)
        query = f'jobsource=index_s&keyword={encoded_keyword}&mode=s'
        search_url = f'{base_url}?{query}&page=1'
        api_url = f'{base_url}api/jobs?{query}&order=16&page=1&pagesize=20&searchJobs=1'
        try:
            with services.CurlCffiService().process('104') as session:
                _get_with_retry(session, search_url).raise_for_status()
                response = _get_with_retry(
                    session, api_url, headers={'Referer': search_url, 'Sec-Fetch-Mode': 'cors'},
                )
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
        feed.id(api_url)
        feed.link(href=f'{base_url}?keyword={encoded_keyword}', rel='alternate')
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
