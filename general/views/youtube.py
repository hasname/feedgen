from concurrent.futures import ThreadPoolExecutor, as_completed
from django.http import HttpResponse
from django.views.generic import View
import dateutil.parser
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


def _fetch_upload_date(session, video_id):
    """Fetch actual upload date from video page JSON-LD."""
    url = 'https://www.youtube.com/watch?v=' + video_id
    try:
        r = session.get(url)
        m = re.search(r'"uploadDate"\s*:\s*"([^"]+)"', r.text)
        if m:
            return video_id, dateutil.parser.parse(m.group(1))
    except Exception:
        pass
    return video_id, None


class YouTubeView(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = 'https://www.youtube.com/results?search_query={}&sp=EgIIAw%253D%253D&hl=en'.format(urllib.parse.quote_plus(keyword))

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

        # Collect video IDs
        video_ids = []
        for item in items:
            try:
                video_ids.append(item['videoRenderer']['videoId'])
            except KeyError:
                pass

        # Fetch actual upload dates in parallel
        upload_dates = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(_fetch_upload_date, s, vid): vid for vid in video_ids}
            for future in as_completed(futures):
                vid, date = future.result()
                if date:
                    upload_dates[vid] = date

        for item in items:
            try:
                video_id = item['videoRenderer']['videoId']

                # author
                author = item['videoRenderer']['longBylineText']['runs'][0]['text']

                # link
                link = 'https://www.youtube.com/watch?v=' + urllib.parse.quote(video_id)

                # img
                img = 'https://i.ytimg.com/vi/' + video_id + '/hqdefault.jpg'

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

                # Use actual upload date from JSON-LD, fall back to relative time
                published = upload_dates.get(video_id)
                if not published:
                    try:
                        published_text = item['videoRenderer']['publishedTimeText']['simpleText']
                        published = _parse_relative_time(published_text)
                    except KeyError:
                        pass

                if published:
                    entry.published(published)
                    entry.updated(published)

            except IndexError:
                pass
            except KeyError:
                pass

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
