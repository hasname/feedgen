from django.http import HttpResponse
from django.views.generic import View
import datetime
import feedgen.feed
import html
import json
import re
import urllib

from .. import services


def _parse_relative_time(text):
    # Strip "Streamed " prefix for past live streams
    text = re.sub(r'^Streamed\s+', '', text)

    m = re.match(r'(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago', text)
    if not m:
        return None

    amount = int(m.group(1))
    unit = m.group(2)

    multipliers = {
        'second': 1,
        'minute': 60,
        'hour': 3600,
        'day': 86400,
        'week': 604800,
        'month': 2592000,
        'year': 31536000,
    }

    seconds = amount * multipliers[unit]
    return datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=seconds)

class YouTubeView(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = 'https://www.youtube.com/results?search_query={}&sp=CAI%253D&hl=en'.format(urllib.parse.quote_plus(keyword))

        title = 'YouTube Search - {}'.format(keyword)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        s = services.RequestsService().process()

        r = s.get(url, headers={'Accept-Language': 'en'})

        m = re.search(r"var ytInitialData = (.*?);?</script>", r.text, re.MULTILINE)
        ytInitialData = m.group(1)
        j = json.loads(ytInitialData)

        items = []
        for loop in j['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']:
            try:
                items += loop['itemSectionRenderer']['contents']
            except KeyError:
                continue

        for item in items:
            try:
                # author
                author = item['videoRenderer']['longBylineText']['runs'][0]['text']

                # link
                link = 'https://www.youtube.com/watch?v=' + urllib.parse.quote(item['videoRenderer']['videoId'])

                # img
                img = 'https://i.ytimg.com/vi/' + item['videoRenderer']['videoId'] + '/hqdefault.jpg'

                # title
                title = item['videoRenderer']['title']['runs'][0]['text']

                # content
                content = '<img alt="{}" src="{}"/>'.format(
                    html.escape(title), html.escape(img)
                )

                entry = feed.add_entry()
                entry.author({'name': author})
                entry.content(content, type='xhtml')
                entry.id(link)
                entry.title(title)
                entry.link(href=link)

                try:
                    published_text = item['videoRenderer']['publishedTimeText']['simpleText']
                    published = _parse_relative_time(published_text)
                    if published:
                        entry.published(published)
                        entry.updated(published)
                except KeyError:
                    pass

            except IndexError:
                pass
            except KeyError:
                pass

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
