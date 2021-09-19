from service_objects.services import Service
import requests

class RequestsService(Service):
    db_transaction = False

    def process(self):
        class sessions(requests.Session):
            def request(self, *args, **kwargs):
                kwargs.setdefault('timeout', 5)
                return super(sessions, self).request(*args, **kwargs)

        s = sessions()
        s.headers.update({'User-Agent': 'feedgen'})

        return s
