from django.http import HttpResponse
from django.views.generic import View
import datetime
import feedgen.feed
import html

from .. import services

class TaipeiMetroTimetableView(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = 'https://web.metro.taipei/img/ALL/timetables/{}.PDF'.format(keyword)
        title = '台北捷運時刻表 - {}'.format(keyword)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            s = services.RequestsService().process()

            r = s.get(url)
            lastmodified = r.headers['last-modified']

            content = '<p>{}</p>'.format(html.escape(lastmodified))
            id = '{}?v={}'.format(url, datetime.fromisoformat(lastmodified))
            title = '台北捷運時刻表 ({}) - {}'.format(keyword, lastmodified)

            entry = feed.add_entry()
            entry.content(content, type='xhtml')
            entry.id(id)
            entry.link(href=url)
            entry.title(title)
        except:
            pass

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
