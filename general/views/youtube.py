from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import html
import lxml.html
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
        body = lxml.html.fromstring(r.text)

        for item in body.cssselect('ol.item-section div.yt-lockup-video'):
            try:
                a = item.cssselect('a[title].spf-link')[0]

                # author
                author = item.cssselect('.yt-lockup-byline a.spf-link.yt-uix-sessionlink')[
                    0
                ].text_content()

                # link
                link = a.get('href')
                if '/' == link[0]:
                    link = 'https://www.youtube.com' + link

                # img
                link_tuple = urllib.parse.urlparse(link)
                d = urllib.parse.parse_qs(link_tuple[4])
                img = 'https://i.ytimg.com/vi/' + d['v'][0] + '/hqdefault.jpg'

                # title
                title = a.get('title')

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
