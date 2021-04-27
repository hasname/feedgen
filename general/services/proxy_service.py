from service_objects.services import Service
import json
import random

class ProxyService(Service):
    db_transaction = False

    def process(self):
        try:
            with open('/tmp/proxylist.json') as fh:
                proxies = json.load(fh)

            return 'http://' + random.choice(proxies)
        except:
            return None
