#!/usr/bin/env python3

import dotenv
import json
import os
import requests

class GenProxy(object):
    def main(self):
        dotenv.load_dotenv()
        url = os.getenv('PROXYLIST_URL')

        res = requests.get(url)
        raw = res.text
        proxies = list(filter(lambda x: x != "", raw.split("\n")))

        with open('/tmp/proxylist.json', 'w+') as fh:
            fh.write(json.dumps(proxies))

if __name__ == '__main__':
    GenProxy().main()
