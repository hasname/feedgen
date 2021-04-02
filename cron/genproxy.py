#!/usr/bin/env python3

import dotenv
import json
import multiprocessing
import os
import requests

class GenProxy(object):
    proxy_list_working = []

    def fetch_target(self, proxy):
        print('* ' + proxy + ' is testing.')
        proxies = {'http': 'http://' + proxy, 'https': 'http://' + proxy}

        headers = {'User-agent': 'feedgen'}
        sample_url = 'https://feedgen.hasname.com/robots.txt'

        try:
            res = requests.get(sample_url, headers=headers, proxies=proxies, timeout=3)

            if res.status_code == 200:
                self.proxy_list_working.append(proxy)
                print('! ' + proxy + ' is working.')

        except:
            pass

    def main(self):
        dotenv.load_dotenv(os.path.dirname(__file__) + '/../.env')

        url = os.getenv('PROXYLIST_URL')
        res = requests.get(url)
        proxy_list = list(filter(lambda x: x != "", res.text.split("\n")))

        pool = multiprocessing.Pool(processes=8)
        pool_outputs = pool.map(self.fetch_target, proxy_list)

        with open('/tmp/proxylist.json', 'w+') as fh:
            fh.write(json.dumps(self.proxy_list_working))

if __name__ == '__main__':
    GenProxy().main()
