#!/usr/bin/env python3

import dotenv
import dotenv.version
import json
import os
import requests

class GenProxy(object):
    def main(self):
        # Ubuntu 18.04
        if dotenv.version.__version__ == '0.7.1':
            dotenv.load_dotenv(os.path.dirname(__file__) + '/../.env')
        else:
            dotenv.load_dotenv(os.path.dirname(__file__) + '/../')

        url = os.getenv('PROXYLIST_URL')

        res = requests.get(url)
        raw = res.text
        proxies = list(filter(lambda x: x != "", raw.split("\n")))

        with open('/tmp/proxylist.json', 'w+') as fh:
            fh.write(json.dumps(proxies))

if __name__ == '__main__':
    GenProxy().main()
