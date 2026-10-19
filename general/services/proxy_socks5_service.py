import os

from service_objects.services import Service


class ProxySocks5Service(Service):
    db_transaction = False

    def process(self):
        return os.getenv('FEEDGEN_HTTP_PROXY')
