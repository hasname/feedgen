import os

from service_objects.services import Service


class ProxySocks5Service(Service):
    db_transaction = False

    def process(self, service=None):
        proxy = os.getenv(f'FEEDGEN_{service.upper()}_PROXY') if service else None
        return proxy or os.getenv('FEEDGEN_HTTP_PROXY') or None
