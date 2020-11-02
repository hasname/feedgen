from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import html
import json
import re
import requests
import urllib

class YouTubeView(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = 'https://www.youtube.com/results?sp=CAISAhAB&search_query={}'.format(urllib.parse.quote_plus(keyword))

        title = 'YouTube Search - {}'.format(keyword)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        s = requests.Session()
        r = s.get(url, headers={'User-agent': 'feedgen'}, timeout=5)

        m = re.search(r"window\[\"ytInitialData\"\] = (.*);$", r.text, re.MULTILINE)
        if m is None:
            items = []
        else:
            ytInitialData = m.group(1)
            j = json.loads(ytInitialData)
            items = j['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']

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

            except IndexError:
                pass

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml')
        res['Cache-Control'] = 'max-age=300,public'

        return res
