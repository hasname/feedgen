from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import html
import lxml.html
import re
import requests

class Job104View(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = 'https://www.104.com.tw/jobs/search/?ro=0&kwop=7&keyword={}&order=11&asc=0&page=1&mode=s'.format(keyword)

        title = '104 搜尋 - {}'.format(keyword)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            s = requests.Session()
            r = s.get(url, headers={'User-agent': 'feedgen'}, timeout=5)
            body = lxml.html.fromstring(r.text)
        except:
            body = lxml.html.fromstring('</html></html>')

        for item in body.cssselect('article.job-list-item'):
            job_company = item.get('data-cust-name')
            job_desc = item.cssselect('p.job-list-item__info')[0].text_content()
            job_title = item.get('data-job-name')
            job_url = item.cssselect('a.js-job-link')[0].get('href')
            job_url = re.sub(r'^//', 'https://', job_url)
            job_url = re.sub(r'&jobsource=\w*$', '', job_url)

            content = '<h3>{}</h3><pre>{}</pre>'.format(
                html.escape(job_company), html.escape(job_desc)
            )

            entry = feed.add_entry()
            entry.content(content, type='xhtml')
            entry.id(job_url)
            entry.link(href=job_url)
            entry.title(job_title)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml')
        res['Cache-Control'] = 'max-age=300,public'

        return res
