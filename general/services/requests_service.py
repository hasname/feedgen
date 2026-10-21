import requests
from service_objects.services import Service

from .proxy_socks5_service import ProxySocks5Service


class RequestsService(Service):
    db_transaction = False

    def process(self, service=None):
        class sessions(requests.Session):
            def request(self, *args, **kwargs):
                kwargs.setdefault('timeout', 10)
                if self.proxies:
                    # Explicit proxies take precedence over HTTP(S)_PROXY.
                    kwargs.setdefault('proxies', self.proxies.copy())
                return super(sessions, self).request(*args, **kwargs)

        s = sessions()
        s.headers.update({'User-Agent': 'feedgen'})

        proxy = ProxySocks5Service().process(service)
        if proxy:
            s.proxies.update({'http': proxy, 'https': proxy})

        return s
