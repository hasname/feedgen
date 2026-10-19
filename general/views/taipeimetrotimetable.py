import datetime
import html

import feedgen.feed
from django.http import HttpResponse
from django.views.generic import View

from .. import services


class TaipeiMetroTimetableView(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = f'https://web.metro.taipei/img/ALL/timetables/{keyword}.PDF'
        title = f'台北捷運時刻表 - {keyword}'

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            s = services.RequestsService().process()

            r = s.get(url)
            lastmodified = r.headers['last-modified']
            t = datetime.datetime.strptime(lastmodified, '%a, %d %b %Y %H:%M:%S %Z')

            content = f'<p>{html.escape(lastmodified)}</p>'
            id = '{}?v={}'.format(url, t.strftime('%s'))
            title = f'台北捷運時刻表 ({keyword}) - {lastmodified}'

            entry = feed.add_entry()
            entry.content(content, type='xhtml')
            entry.id(id)
            entry.link(href=url)
            entry.title(title)
            entry.updated(lastmodified)
        except Exception:
            pass

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
