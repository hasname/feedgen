#!/usr/bin/env python3

import dotenv
import json
import multiprocessing
import os
import requests

class GenProxy(object):
    def fetch_target(self, proxy):
        print('* ' + proxy + ' is testing.')
        proxies = {'http': 'http://' + proxy, 'https': 'http://' + proxy}

        headers = {'User-agent': 'feedgen'}
        sample_url = 'https://feedgen.hasname.com/robots.txt'

        try:
            res = requests.get(sample_url, headers=headers, proxies=proxies, timeout=3)

            if res.status_code == 200:
                print('! ' + proxy + ' is working.')
                return proxy

        except:
            pass

        return None

    def main(self):
        dotenv.load_dotenv(os.path.dirname(__file__) + '/../.env')

        url = os.getenv('PROXYLIST_URL')
        res = requests.get(url)
        proxy_list = list(filter(lambda x: x != "", res.text.split("\n")))

        pool = multiprocessing.Pool(processes=4)
        proxy_list_working = list(filter(lambda x: x is not None, pool.map(self.fetch_target, proxy_list)))

        with open('/tmp/proxylist.json', 'w+') as fh:
            fh.write(json.dumps(proxy_list_working))

if __name__ == '__main__':
    GenProxy().main()
