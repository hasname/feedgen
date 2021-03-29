#!/usr/bin/env python3

import dotenv
import json
import os
import requests

class GenProxy(object):
    def main(self):
        dotenv.load_dotenv(os.path.dirname(__file__) + '/../.env')

        sample_url = 'https://feedgen.hasname.com/robots.txt'
        url = os.getenv('PROXYLIST_URL')

        res = requests.get(url)
        raw = res.text
        proxy_list = list(filter(lambda x: x != "", raw.split("\n")))
        proxy_list_working = []

        for proxy in proxy_list:
            print('* ' + proxy + ' is testing.')
            proxies = {'http': 'http://' + proxy, 'https': 'http://' + proxy}

            try:
                res = requests.get(sample_url, headers={'User-agent': 'feedgen'}, proxies=proxies, timeout=3)

                if res.status_code == 200:
                    proxy_list_working.append(proxy)
                    print('! ' + proxy + ' is working.')

            except:
                pass

        with open('/tmp/proxylist.json', 'w+') as fh:
            fh.write(json.dumps(proxies_working))

if __name__ == '__main__':
    GenProxy().main()
