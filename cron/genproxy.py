#!/usr/bin/env python3

import dotenv
import json
import os
import requests

class GenProxy(object):
    def main(self):
        # Ubuntu 18.04
        try:
            import dotenv.version
            dotenv.load_dotenv(os.path.dirname(__file__) + '/../')
        except:
            dotenv.load_dotenv(os.path.dirname(__file__) + '/../.env')

        url = os.getenv('PROXYLIST_URL')

        res = requests.get(url)
        raw = res.text
        proxies = list(filter(lambda x: x != "", raw.split("\n")))

        with open('/tmp/proxylist.json', 'w+') as fh:
            fh.write(json.dumps(proxies))

if __name__ == '__main__':
    GenProxy().main()
