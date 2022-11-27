from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import html
import lxml.html
import re

from .. import services

class Rent591View(View):
    def get(self, *args, **kwargs):
        region = kwargs['region']
        keyword = kwargs['keyword']

        # Support query string to filter results.
        qs = self.request.META.get('QUERY_STRING', '')
        if qs != '':
            qs = '&' + qs

        url = 'https://rent.591.com.tw/?kind=0&order=posttime&orderType=desc&region={}&keywords={}{}'.format(region, keyword, qs)

        if qs == '':
            title = '591 出租搜尋 - {}'.format(keyword)
        else:
            title = '591 出租搜尋 - {} ({})'.format(keyword, qs)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            s = services.RequestsService().process()

            r = s.get(url)
            text = r.text
        except:
            text = '<html></html>'

        body = lxml.html.fromstring(text)

        items = body.cssselect('#content > ul')

        for item in items:
            item_metainfo = item.cssselect('.infoContent .lightBox')[0].text_content()
            item_area = re.search(r'([\.0-9]+坪)', item_metainfo).group(1)
            item_desc = item.text_content()
            item_img = item.cssselect('.imageBox img')[0].get('data-original')
            item_price = item.cssselect('.price')[0].text_content()
            item_title = item.cssselect('.infoContent')[0].text_content()
            item_url = item.cssselect('a')[0].get('href')
            item_url = re.sub(r'^//', 'https://', item_url)

            item_price_num = item_price.replace(',', '')
            item_price_num = float(re.sub(r' .*', '', item_price_num))
            item_area_num = float(re.sub(r'坪.*', '', item_area))
            item_unitprice = int(item_price_num / item_area_num)

            content = '<img alt="{}" src="{}"/><br/>{}<br/>{}'.format(
                html.escape(item_title),
                html.escape(item_img),
                html.escape(item_title),
                html.escape(item_desc)
            )

            entry = feed.add_entry()
            entry.content(content, type='xhtml')
            entry.id(item_url)
            entry.link(href=item_url)
            entry.title('${}/坪 - {} - {}'.format(item_unitprice, item_area, item_title))

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
