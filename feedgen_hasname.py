#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor
from requests_futures.sessions import FuturesSession

import base36
import bottle
import configparser
import datetime
import feedgen.feed
import html
import lxml.html
import json
import os
import re
import requests
import sentry_sdk
import urllib

# Variables
user_agent = 'Mozilla/5.0'

app = application = bottle.Bottle()


def init_sentry():
    config = configparser.ConfigParser()
    config.read('{}/.config/feedgen/sentry.ini'.format(os.environ['HOME']))

    sentry_sdk.init(config['default']['sentry_url'])


@app.route('/')
def index():
    bottle.redirect('https://github.com/hasname/feedgen')


@app.route('/robots.txt')
def robotstxt():
    bottle.response.set_header('Content-Type', 'text/plain')
    return '#\nUser-agent: *\nDisallow: /\n'


@app.route('/bookwalker-lightnovel')
def bookwalker_lightnovel():
    url = 'https://www.bookwalker.com.tw/more/fiction/1/3'

    title = 'BOOKWALKER 輕小說'

    feed = feedgen.feed.FeedGenerator()
    feed.author({'name': 'Feed Generator'})
    feed.id(url)
    feed.link(href=url, rel='alternate')
    feed.title(title)

    r = requests.get(url, headers={'User-agent': user_agent}, timeout=5)
    body = lxml.html.fromstring(r.text)

    for item in body.cssselect('.bwbookitem a'):
        img = item.cssselect('img')[0]
        img.set('src', img.get('data-src'))
        content = lxml.etree.tostring(item, encoding='unicode')
        book_title = item.get('title')
        book_url = item.get('href')

        entry = feed.add_entry()
        entry.content(content, type='xhtml')
        entry.id(book_url)
        entry.title(book_title)
        entry.link(href=book_url)

    bottle.response.set_header('Cache-Control', 'max-age=300,public')
    bottle.response.set_header('Content-Type', 'application/atom+xml')

    return feed.atom_str()


@app.route('/dcard/top')
def dcardtop():
    url = 'https://www.dcard.tw/f'

    title = 'Dcard Top'

    feed = feedgen.feed.FeedGenerator()
    feed.author({'name': 'Feed Generator'})
    feed.id(url)
    feed.link(href=url, rel='alternate')
    feed.title(title)

    r = requests.get(url, headers={'User-agent': user_agent}, timeout=5)
    body = lxml.html.fromstring(r.text)

    for post in body.cssselect('div[class^="PostList_entry_"]'):
        try:
            post_author = post.cssselect('div[class^="PostAuthorHeader_meta_"]')[0].text_content()
            post_excerpt = post.cssselect('div[class^="PostEntry_excerpt_"]')[0].text_content()
            post_title = post.cssselect('h3[class^="PostEntry_title_"]')[0].text_content()
            post_url = post.cssselect('a[class^="PostEntry_root_"]')[0].get('href')

            if post_url.startswith('/'):
                post_url = 'https://www.dcard.tw' + post_url

            content = html.escape(post_excerpt)

            entry = feed.add_entry()
            entry.author({'name': post_author})
            entry.content(content, type='xhtml')
            entry.id(post_url)
            entry.link(href=post_url)
            entry.title(post_title)

        except IndexError:
            pass

    bottle.response.set_header('Cache-Control', 'max-age=300,public')
    bottle.response.set_header('Content-Type', 'application/atom+xml')

    return feed.atom_str()


@app.route('/104/<keyword>')
def job104(keyword):
    url = 'https://www.104.com.tw/jobs/search/?ro=0&kwop=7&keyword={}&order=11&asc=0&page=1&mode=s'.format(
        keyword
    )

    title = '104 搜尋 - {}'.format(keyword)

    feed = feedgen.feed.FeedGenerator()
    feed.author({'name': 'Feed Generator'})
    feed.id(url)
    feed.link(href=url, rel='alternate')
    feed.title(title)

    r = requests.get(url, headers={'User-agent': user_agent}, timeout=5)
    body = lxml.html.fromstring(r.text)

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

    bottle.response.set_header('Cache-Control', 'max-age=300,public')
    bottle.response.set_header('Content-Type', 'application/atom+xml')

    return feed.atom_str()


@app.route('/1111/<keyword>')
def job1111(keyword):
    url = 'https://www.1111.com.tw/job-bank/job-index.asp?flag=13&ks={}&fs=1&si=1&ts=4&col=da&sort=desc'.format(
        urllib.parse.quote_plus(keyword)
    )

    title = '1111 搜尋 - {}'.format(keyword)

    feed = feedgen.feed.FeedGenerator()
    feed.author({'name': 'Feed Generator'})
    feed.id(url)
    feed.link(href=url, rel='alternate')
    feed.title(title)

    r = requests.get(url, headers={'User-agent': user_agent}, timeout=5)
    r.encoding = 'utf-8'
    body = lxml.html.fromstring(r.text)

    for item in body.cssselect('li.digest'):
        a = item.cssselect('a.mobiFullLInk')[0]
        job_title = a.get('title')
        job_url = a.get('href')
        if job_url.startswith('//'):
            job_url = 'https:' + job_url

        job_company = item.cssselect('.jbInfoin h4 a')[0].get('title')

        job_desc = item.cssselect('.jbInfoTxt')[0].text_content()
        content = '<h3>{}</h3><p>{}</p>'.format(
            html.escape(job_company), html.escape(job_desc)
        )

        entry = feed.add_entry()
        entry.content(content, type='xhtml')
        entry.id(job_url)
        entry.link(href=job_url)
        entry.title(job_title)

    bottle.response.set_header('Cache-Control', 'max-age=300,public')
    bottle.response.set_header('Content-Type', 'application/atom+xml')

    return feed.atom_str()


@app.route('/518/<keyword>')
def job518(keyword):
    url = 'https://www.518.com.tw/job-index-P-1.html?i=1&am=1&ad={}&orderType=1&orderField=8'.format(
        urllib.parse.quote_plus(keyword)
    )

    title = '518 搜尋 - {}'.format(keyword)

    feed = feedgen.feed.FeedGenerator()
    feed.author({'name': 'Feed Generator'})
    feed.id(url)
    feed.link(href=url, rel='alternate')
    feed.title(title)

    r = requests.get(url, headers={'User-agent': user_agent}, timeout=5)
    body = lxml.html.fromstring(r.text)

    for item in body.cssselect('#listContent > ul'):
        try:
            a = item.cssselect('li.title a')[0]
            job_title = a.getchildren()[0].text_content()

            job_url = a.get('href')
            job_url = re.sub('\\?.*', '', job_url)

            job_company = item.cssselect('li.company')[0].text_content()

            job_desc = item.cssselect('li.sumbox')[0].text_content()
            content = '<h3>{}</h3><p>{}</p>'.format(
                html.escape(job_company), html.escape(job_desc)
            )

            entry = feed.add_entry()
            entry.content(content, type='xhtml')
            entry.id(job_url)
            entry.link(href=job_url)
            entry.title(job_title)

        except IndexError:
            pass

    bottle.response.set_header('Cache-Control', 'max-age=300,public')
    bottle.response.set_header('Content-Type', 'application/atom+xml')

    return feed.atom_str()


@app.route('/instagram/<username>')
def instagram(username):
    url = 'https://www.instagram.com/{}'.format(urllib.parse.quote_plus(username))

    title = 'Instagram - {}'.format(username)

    feed = feedgen.feed.FeedGenerator()
    feed.author({'name': 'Feed Generator'})
    feed.id(url)
    feed.link(href=url, rel='alternate')
    feed.title(title)

    r = requests.get(url, headers={'User-agent': user_agent}, timeout=5)
    ig_data = re.search(r"^<script type=\"text/javascript\">window\._sharedData = (.*?);</script>", r.text, re.MULTILINE).group(1)
    data = json.loads(ig_data)

    for edge in data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges']:
        item_created_at = edge['node']['taken_at_timestamp']
        item_image = edge['node']['display_url']
        item_text = edge['node']['edge_media_to_caption']['edges'][0]['node']['text']
        item_url = 'https://www.instagram.com/p/{}'.format(edge['node']['shortcode'])

        content = '<p>{}</p><img alt="" src="{}"/>'.format(html.escape(item_text), html.escape(item_image))

        entry = feed.add_entry()
        entry.content(content, type='xhtml')
        entry.id(item_url)
        entry.link(href=item_url)
        entry.published(datetime.datetime.fromtimestamp(item_created_at, datetime.timezone.utc))
        entry.title(item_text)

    bottle.response.set_header('Cache-Control', 'max-age=300,public')
    bottle.response.set_header('Content-Type', 'application/atom+xml')

    return feed.atom_str()


@app.route('/pchome/<keyword>')
def pchome(keyword):
    url = 'https://ecshweb.pchome.com.tw/search/v3.3/all/results?q={}&page=1&sort=new/dc'.format(
        urllib.parse.quote_plus(keyword)
    )

    title = 'PChome 搜尋 - {}'.format(keyword)

    feed = feedgen.feed.FeedGenerator()
    feed.author({'name': 'Feed Generator'})
    feed.id(url)
    feed.link(href=url, rel='alternate')
    feed.title(title)

    r = requests.get(url, headers={'User-agent': user_agent}, timeout=5)
    body = json.loads(r.text)

    for prod in body['prods']:
        # Product name & description
        prod_name = prod['name']
        prod_desc = prod['describe']
        prod_author = prod['author']

        # URL
        if prod['cateId'][0] == 'D':
            prod_url = 'https://24h.pchome.com.tw/prod/' + prod['Id']
        else:
            prod_url = 'https://mall.pchome.com.tw/prod/' + prod['Id']
        img_url = 'https://a.ecimg.tw%s' % (prod['picB'])

        content = '{}<br/><img alt="{}" src="{}"/>'.format(
            html.escape(prod_desc), html.escape(prod_name), html.escape(img_url)
        )

        entry = feed.add_entry()
        entry.author({'name': prod_author})
        entry.content(content, type='xhtml')
        entry.id(prod_url)
        entry.link(href=prod_url)
        entry.title(prod_name)

    bottle.response.set_header('Cache-Control', 'max-age=300,public')
    bottle.response.set_header('Content-Type', 'application/atom+xml')

    return feed.atom_str()


@app.route('/pchome-lightnovel')
def pchome_lightnovel():
    url = 'https://ecapi.pchome.com.tw/cdn/ecshop/prodapi/v2/newarrival/DJAZ/prod&offset=1&limit=20&fields=Id,Nick,Pic,Price,Discount,isSpec,Name,isCarrier,isSnapUp,isBigCart&_callback=jsonp_prodlist?_callback=jsonp_prodlist'

    title = 'PChome 輕小說'

    feed = feedgen.feed.FeedGenerator()
    feed.author({'name': 'Feed Generator'})
    feed.id(url)
    feed.link(href=url, rel='alternate')
    feed.title(title)

    r = requests.get(url, headers={'User-agent': user_agent}, timeout=5)
    body = re.match(r'^[^\[]*(\[.*\])[^\[]*$', r.text).group(1)
    items = json.loads(body)

    for item in items:
        content = '{}<br/><img alt="{}" src="https://a.ecimg.tw{}"/>'.format(
            html.escape(item['Nick']),
            html.escape(item['Nick']),
            html.escape(item['Pic']['B']),
        )
        book_title = item['Nick']
        book_url = 'https://24h.pchome.com.tw/books/prod/{}'.format(
            urllib.parse.quote_plus(item['Id'])
        )

        entry = feed.add_entry()
        entry.content(content, type='xhtml')
        entry.id(book_url)
        entry.title(book_title)
        entry.link(href=book_url)

    bottle.response.set_header('Cache-Control', 'max-age=300,public')
    bottle.response.set_header('Content-Type', 'application/atom+xml')

    return feed.atom_str()


@app.route('/plurk/top/<lang>')
def plurktop(lang):
    url = 'https://www.plurk.com/Stats/topReplurks?period=day&lang={}&limit=20'.format(
        urllib.parse.quote_plus(lang)
    )

    title = 'Plurk Top ({})'.format(lang)

    feed = feedgen.feed.FeedGenerator()
    feed.author({'name': 'Feed Generator'})
    feed.id(url)
    feed.link(href=url, rel='alternate')
    feed.title(title)

    r = requests.get(url, headers={'User-agent': user_agent}, timeout=5)
    body = json.loads(r.text)

    for (x, stat) in body['stats']:
        url = 'https://www.plurk.com/p/' + base36.dumps(stat['id'])

        content = stat['content']
        content = re.sub(r' height="\d+(px)?"', ' ', content)
        content = re.sub(r' width="\d+(px)?"', ' ', content)

        entry = feed.add_entry()
        entry.author({'name': stat['owner']['full_name']})
        entry.content(content, type='CDATA')
        entry.id(url)
        entry.link(href=url)
        entry.published(stat['posted'])
        entry.title(stat['content_raw'])

    bottle.response.set_header('Cache-Control', 'max-age=300,public')
    bottle.response.set_header('Content-Type', 'application/atom+xml')

    return feed.atom_str()


@app.route('/shopee/<keyword>')
def shopee(keyword):
    url = 'https://shopee.tw/api/v2/search_items/?by=ctime&keyword={}&limit=50&newest=0&order=desc&page_type=search'.format(
        urllib.parse.quote_plus(keyword)
    )

    title = '蝦皮搜尋 - {}'.format(keyword)

    feed = feedgen.feed.FeedGenerator()
    feed.author({'name': 'Feed Generator'})
    feed.id(url)
    feed.link(href=url, rel='alternate')
    feed.title(title)

    r = requests.get(url, headers={'User-agent': user_agent}, timeout=5)
    body = json.loads(r.text)

    session = FuturesSession(executor=ThreadPoolExecutor(max_workers=10))
    futures = []

    for item in body['items']:
        itemid = item['itemid']
        name = item['name']
        shopid = item['shopid']

        itemapi_url = 'https://shopee.tw/api/v2/item/get?itemid=%d&shopid=%d' % (
            itemid,
            shopid,
        )
        futures.append(
            session.get(itemapi_url, headers={'User-agent': user_agent}, timeout=5)
        )

    for f in futures:
        r = f.result()
        item = json.loads(r.text)['item']

        itemid = item['itemid']
        name = item['name']
        shopid = item['shopid']

        prod_url = 'https://shopee.tw/product/%d/%d' % (shopid, itemid)
        img_url = 'https://cf.shopee.tw/file/%s' % (item['image'])

        content = '{}<br/><img alt="{}" src="{}"/>'.format(
            html.escape(name), html.escape(name), html.escape(img_url)
        )

        entry = feed.add_entry()
        entry.content(content, type='xhtml')
        entry.id(prod_url)
        entry.link(href=prod_url)
        entry.title(name)

    bottle.response.set_header('Cache-Control', 'max-age=300,public')
    bottle.response.set_header('Content-Type', 'application/atom+xml')

    return feed.atom_str()


@app.route('/youtube/<keyword>')
def youtube(keyword):
    url = 'https://www.youtube.com/results?sp=CAI%%253D&search_query={}'.format(
        urllib.parse.quote_plus(keyword)
    )

    title = 'YouTube Search - {}'.format(keyword)

    feed = feedgen.feed.FeedGenerator()
    feed.author({'name': 'Feed Generator'})
    feed.id(url)
    feed.link(href=url, rel='alternate')
    feed.title(title)

    r = requests.get(url)
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

    bottle.response.set_header('Cache-Control', 'max-age=300,public')
    bottle.response.set_header('Content-Type', 'application/atom+xml')

    return feed.atom_str()


if __name__ == '__main__':
    if os.environ.get('PORT'):
        port = int(os.environ.get('PORT'))
    else:
        port = 8080

    bottle.run(app=app, host='0.0.0.0', port=port)
elif 'CI' not in os.environ:
    init_sentry()
