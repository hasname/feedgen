#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor
from requests_futures.sessions import FuturesSession

import base36
import bottle
import feedgen.feed
import html
import lxml.etree
import lxml.html
import json
import os
import re
import requests
import urllib

app = application = bottle.Bottle()

@app.route('/')
def index():
    bottle.redirect('https://github.com/gslin/feedgen')

@app.route('/robots.txt')
def robotstxt():
    bottle.response.set_header('Content-Type', 'text/plain')
    return '#\nUser-agent: *\nDisallow: /\n'

@app.route('/104/<keyword>')
def job104(keyword):
    url = 'https://www.104.com.tw/jobs/search/?ro=0&kwop=7&keyword={}&order=2&asc=0&page=1&mode=s'.format(urllib.parse.quote_plus(keyword))

    title = '104 搜尋 - {}'.format(keyword)

    feed = feedgen.feed.FeedGenerator()
    feed.author({'name': 'Feed Generator'})
    feed.id(url)
    feed.link(href=url, rel='alternate')
    feed.title(title)

    r = requests.get(url, headers={'User-agent': 'Mozilla/5.0'}, timeout=5)
    body = lxml.html.fromstring(r.text)

    session = FuturesSession(executor=ThreadPoolExecutor(max_workers=10))
    futures = []

    for item in body.cssselect('article.job-list-item'):
        a = item.cssselect('a.js-job-link')[0]

        href = a.get('href')
        href = re.sub(r'&jobsource=\w+', '', href)
        if href.startswith('//'):
            href = 'https:' + href
        job_url = href

        futures.append(session.get(job_url, headers={'User-agent': 'Mozilla/5.0'}, timeout=5))

    for f in futures:
        r = f.result()
        body = lxml.html.fromstring(r.text)

        job_title = body.cssselect('#job h1')[0].text_content()
        job_url = r.url

        job_company = lxml.etree.tostring(body.cssselect('.company')[0]).decode('utf-8')
        job_desc = lxml.etree.tostring(body.cssselect('.grid-left .main')[0]).decode('utf-8')

        content = '<p>{}</p><p>{}</p>'.format(html.escape(job_company), html.escape(job_desc))

        entry = feed.add_entry()
        entry.content(content, type='xhtml')
        entry.id(job_url)
        entry.link(href=job_url)
        entry.title(job_title)

    bottle.response.set_header('Cache-Control', 'max-age=300,public')
    bottle.response.set_header('Content-Type', 'application/atom+xml')

    return feed.atom_str()

@app.route('/pchome/<keyword>')
def pchome(keyword):
    url = 'https://ecshweb.pchome.com.tw/search/v3.3/all/results?q=%s&page=1&sort=new/dc' % (urllib.parse.quote_plus(keyword))

    title = 'PChome 搜尋 - {}'.format(keyword)

    feed = feedgen.feed.FeedGenerator()
    feed.author({'name': 'Feed Generator'})
    feed.id(url)
    feed.link(href=url, rel='alternate')
    feed.title(title)

    r = requests.get(url, headers={'User-agent': 'Mozilla/5.0'}, timeout=5)
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

        content = '%s<br/><img alt="" src="%s"/>' % (html.escape(prod_desc), html.escape(img_url))

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

    r = requests.get(url, headers={'User-agent': 'Mozilla/5.0'}, timeout=5)
    body = re.match(r'^[^\[]*(\[.*\])[^\[]*$', r.text).group(1)
    items = json.loads(body)

    for item in items:
        content = '{}<br/><img alt="" src="https://a.ecimg.tw{}"/>'.format(html.escape(item['Nick']), html.escape(item['Pic']['B']))
        book_title = item['Nick']
        book_url = 'https://24h.pchome.com.tw/books/prod/{}'.format(urllib.parse.quote_plus(item['Id']))

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
    url = 'https://www.plurk.com/Stats/topReplurks?period=day&lang=%s&limit=20' % (urllib.parse.quote_plus(lang))

    title = 'Plurk Top ({})'.format(lang)

    feed = feedgen.feed.FeedGenerator()
    feed.author({'name': 'Feed Generator'})
    feed.id(url)
    feed.link(href=url, rel='alternate')
    feed.title(title)

    r = requests.get(url, headers={'User-agent': 'Mozilla/5.0'}, timeout=5)
    body = json.loads(r.text)

    for (x, stat) in body['stats']:
        url = 'https://www.plurk.com/p/' + base36.dumps(stat['id'])

        entry = feed.add_entry()
        entry.author({'name': stat['owner']['full_name']})
        entry.content(stat['content'], type='CDATA')
        entry.id(url)
        entry.link(href=url)
        entry.published(stat['posted'])
        entry.title(stat['content_raw'])

    bottle.response.set_header('Cache-Control', 'max-age=300,public')
    bottle.response.set_header('Content-Type', 'application/atom+xml')

    return feed.atom_str()

@app.route('/shopee/<keyword>')
def shopee(keyword):
    url = 'https://shopee.tw/api/v2/search_items/?by=ctime&keyword=%s&limit=50&newest=0&order=desc&page_type=search' % (urllib.parse.quote_plus(keyword))

    title = '蝦皮搜尋 - {}'.format(keyword)

    feed = feedgen.feed.FeedGenerator()
    feed.author({'name': 'Feed Generator'})
    feed.id(url)
    feed.link(href=url, rel='alternate')
    feed.title(title)

    r = requests.get(url, headers={'User-agent': 'Mozilla/5.0'}, timeout=5)
    body = json.loads(r.text)

    session = FuturesSession(executor=ThreadPoolExecutor(max_workers=10))
    futures = []

    for item in body['items']:
        itemid = item['itemid']
        name = item['name']
        shopid = item['shopid']

        itemapi_url = 'https://shopee.tw/api/v2/item/get?itemid=%d&shopid=%d' % (itemid, shopid)
        futures.append(session.get(itemapi_url, headers={'User-agent': 'Mozilla/5.0'}, timeout=5))

    for f in futures:
        r = f.result()
        item = json.loads(r.text)['item']

        itemid = item['itemid']
        name = item['name']
        shopid = item['shopid']

        prod_url = 'https://shopee.tw/%s-i.%d.%d' % (urllib.parse.quote_plus(name), shopid, itemid)
        img_url = 'https://cf.shopee.tw/file/%s' % (item['image'])

        content = '%s<br/><img alt="" src="%s"/>' % (html.escape(name), html.escape(img_url))

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
    url = 'https://www.youtube.com/results?sp=CAI%%253D&search_query=%s' % (urllib.parse.quote_plus(keyword))

    title = 'YouTube Search - {}'.format(keyword)

    feed = feedgen.feed.FeedGenerator()
    feed.author({'name': 'Feed Generator'})
    feed.id(url)
    feed.link(href=url, rel='alternate')
    feed.title(title)

    r = requests.get(url);
    body = lxml.html.fromstring(r.text)

    for item in body.cssselect('ol.item-section div.yt-lockup-video'):
        try:
            a = item.cssselect('a[title].spf-link')[0]

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
            content = '%s<br/><img alt="%s" src="%s"/>' % (html.escape(title), html.escape(title), html.escape(img))

            entry = feed.add_entry()
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
