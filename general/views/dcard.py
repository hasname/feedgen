import html
import json
import logging
import re
from urllib.parse import quote

import feedgen.feed
import lxml.html
from django.http import HttpResponse
from django.views.generic import View

from .. import services

logger = logging.getLogger(__name__)
BASE_URL = 'https://www.dcard.tw'
PAGING_URL = f'{BASE_URL}/service/api/v2/globalPaging'


def _objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _objects(child)


def _popular_list_key(body):
    # React Flight embeds JSON strings across script chunks. Decode, never eval.
    decoder = json.JSONDecoder()
    chunks = []
    for script in body.xpath('//script[not(@src)]/text()'):
        for match in re.finditer(r'self\.__next_f\.push\(', script):
            chunk, _ = decoder.raw_decode(script[match.end():])
            if len(chunk) > 1 and chunk[0] == 1 and isinstance(chunk[1], str):
                chunks.append(chunk[1])
    stream = ''.join(chunks)
    for match in re.finditer(r'^[0-9a-f]+:(?=[\[{])', stream, re.MULTILINE):
        try:
            record, _ = decoder.raw_decode(stream[match.end():])
        except json.JSONDecodeError:
            continue
        for query in _objects(record):
            key = query.get('queryKey')
            if not isinstance(key, list) or key[:2] != ['tab', 'config']:
                continue
            for tab in _objects(query['state']['data']):
                if tab.get('alias') == 'popular' and tab.get('listType') == 'globalPaging':
                    list_key = tab['payload']['listKey']
                    if isinstance(list_key, str) and list_key:
                        return list_key
    raise ValueError('Cannot find Dcard popular list configuration')


def _fetch_posts(session, url):
    response = session.get(url)
    response.raise_for_status()
    body = lxml.html.fromstring(response.content)
    params = {
        'enrich': 'true',
        'forumLogo': 'true',
        'pinnedPosts': 'widget',
        'platform': 'mobileweb',
        'listKey': _popular_list_key(body),
    }
    response = session.get(f'{PAGING_URL}/head', params=params)
    response.raise_for_status()
    head = response.json()['head']
    if not isinstance(head, str) or not head:
        raise ValueError('Invalid Dcard page key')
    response = session.get(f'{PAGING_URL}/page', params={
        **params, 'pageKey': head, 'offset': 0, 'lang': body.get('lang') or 'zh-TW',
    })
    response.raise_for_status()
    widgets = response.json()['widgets']
    if not isinstance(widgets, list):
        raise TypeError('Invalid Dcard widgets')
    posts = []
    for widget in widgets:
        # Other widgets contain ads, recommendations, and pinned/featured posts.
        if 'forumList' in widget:
            for item in widget['forumList']['items']:
                post = item.get('post')
                if post is not None:
                    posts.append(post)
    if widgets and not posts:
        raise ValueError('No article data in Dcard widgets')
    return posts


def _feed(url, title, include_forum=False):
    feed = feedgen.feed.FeedGenerator()
    feed.author({'name': 'Feed Generator'})
    feed.id(url)
    feed.link(href=url, rel='alternate')
    feed.title(title)

    try:
        with services.CfsolveService().process('dcard') as session:
            posts = _fetch_posts(session, url)
        seen = set()
        for post in posts:
            post_id = post['id']
            if post_id in seen:
                continue
            seen.add(post_id)
            post_url = f'{BASE_URL}/f/{quote(post["forumAlias"], safe="")}/p/{quote(str(post_id), safe="")}'
            post_title = post['title']
            if include_forum:
                post_title = f'[{post["forumName"]}] {post_title}'
            content = f'<p>{html.escape(post["excerpt"])}</p>'
            image_url = next((
                media['url'] for media in post.get('mediaMeta', [])
                if media.get('type', '').startswith('image/')
                and media.get('url', '').startswith(('https://', 'http://'))
            ), None)
            if image_url:
                content = f'<img alt="{html.escape(post_title)}" src="{html.escape(image_url)}"/>{content}'

            entry = feed.add_entry(order='append')
            entry.content(content, type='xhtml')
            entry.id(post_url)
            entry.title(post_title)
            entry.link(href=post_url)

        response = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
    except Exception:
        logger.exception('Failed to fetch or parse Dcard feed')
        return HttpResponse('Service Unavailable', status=503, headers={'Cache-Control': 'no-store'})

    response['Cache-Control'] = 'max-age=300,public'
    return response


class DcardBoardView(View):
    def get(self, *args, **kwargs):
        board = kwargs['board']
        return _feed(f'{BASE_URL}/f/{quote(board, safe="")}', f'Dcard 看板 - {board}')


class DcardMainView(View):
    def get(self, *args, **kwargs):
        return _feed(f'{BASE_URL}/f', 'Dcard 首頁', include_forum=True)
