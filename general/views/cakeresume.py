from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import html
import lxml
import re
import urllib

from .. import services

class CakeResumeView(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = 'https://www.cakeresume.com/jobs/{}?location_list%5B0%5D=Taiwan&order=latest'.format(urllib.parse.quote_plus(keyword))

        title = 'CakeResume 搜尋 - {}'.format(keyword)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            s = services.RequestsService().process()

            r = s.get(url)
            body = lxml.html.fromstring(r.text)
            items = body.cssselect('div[class^="JobSearchItem_wrapper__"]')
        except:
            items = []

        for item in items:
            job_company = item.cssselect('a[class^="JobSearchItem_companyName__"]')[0].text_content()
            job_desc = item.cssselect('div[class^="JobSearchItem_description__"]')[0].text_content()
            job_features = item.cssselect('div[class^="JobSearchItem_features__"]')[0].text_content()
            job_link = item.cssselect('a[class^="JobSearchItem_jobTitle__"]')[0].get('href')
            job_title = item.cssselect('a[class^="JobSearchItem_jobTitle__"]')[0].text_content()

            # "/"-prefix but not "//"-prefix:
            if re.match(r'^/($|[^/])', job_link):
                job_link = 'https://www.cakeresume.com' + job_link

            item_author = job_company
            item_content = '<p>{}</p><p>{}</p>'.format(html.escape(job_features), html.escape(job_desc))
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
