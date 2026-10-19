import requests
from service_objects.services import Service


class RequestsService(Service):
    db_transaction = False

    def process(self):
        class sessions(requests.Session):
            def request(self, *args, **kwargs):
                kwargs.setdefault('timeout', 10)
                return super(sessions, self).request(*args, **kwargs)

        s = sessions()
        s.headers.update({'User-Agent': 'feedgen'})

        return s
