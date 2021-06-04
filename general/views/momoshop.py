from django.http import HttpResponse
from django.views.generic import View
import feedgen.feed
import html
import json
import requests
import time
import urllib

class MomoshopView(View):
    def get(self, *args, **kwargs):
        keyword = kwargs['keyword']

        url = 'https://www.momoshop.com.tw/search/searchShop.jsp?keyword={}&searchType=1&cateLevel=0&cateCode=&curPage=1&_isFuzzy=0&showType=chessboardType'.format(urllib.parse.quote_plus(keyword))

        title = 'Momoshop 搜尋 - {}'.format(keyword)

        feed = feedgen.feed.FeedGenerator()
        feed.author({'name': 'Feed Generator'})
        feed.id(url)
        feed.link(href=url, rel='alternate')
        feed.title(title)

        try:
            s = requests.Session()

            # Environment cookie.
            r = s.get('https://www.momoshop.com.tw/', headers={'User-agent': 'feedgen'}, timeout=5)

            # Get the actual content.
            now = int(time.time())
            data = {
                'flag': 2018,
                'data': {
                    'specialGoodsType': '',
                    'searchValue': keyword,
                    'cateCode': '',
                    'cateLevel': '0',
                    'cp': 'N',
                    'NAM': 'N',
                    'first': 'N',
                    'freeze': 'N',
                    'superstore': 'N',
                    'tvshop': 'N',
                    'china': 'N',
                    'tomorrow': 'N',
                    'stockYN': 'N',
                    'prefere': 'N',
                    'threeHours': 'N',
                    'showType': 'chessboardType',
                    'curPage': '1',
                    'priceS': '0',
                    'priceE': '9999999',
                    'searchType': '4',
                    'reduceKeyword': '',
                    'isFuzzy': '0',
                    'rtnCateDatainfo':  {
                        'cateCode': '',
                        'cateLv': '0',
                        'keyword': keyword,
                        'curPage': '1',
                        'historyDoPush': False,
                        'timestamp': now,
                    },
                }
            }
            url = 'https://www.momoshop.com.tw/ajax/ajaxTool.jsp?n=2018'
            r = s.post(url, data={'data': json.dumps(data)}, headers={'Referer': 'https://www.momoshop.com.tw/', 'User-agent': 'feedgen'}, timeout=5)
            body = json.loads(r.text)
        except:
            return HttpResponse('Service Unavailable', status=503)

        for item in body['rtnData']['searchResult']['rtnSearchData']['goodsInfoList']:
            # Product name & description
            item_name = item['goodsName']
            item_title = '(${}) {}'.format(item['goodsPrice'], item_name)
            item_url = 'https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code={}'.format(item['goodsCode'])

            content = '<img alt="{}" src="{}"/>'.format(html.escape(item_name), html.escape(item['imgUrl']))

            entry = feed.add_entry()
            entry.content(content, type='xhtml')
            entry.id(item_url)
            entry.link(href=item_url)
            entry.title(item_title)

        res = HttpResponse(feed.atom_str(), content_type='application/atom+xml; charset=utf-8')
        res['Cache-Control'] = 'max-age=300,public'

        return res
