import requests
from curl_cffi import requests as curl_requests
from curl_cffi.requests.impersonate import BrowserType
from service_objects.services import Service

from .proxy_socks5_service import ProxySocks5Service

# Chrome impersonation targets verified against 104's Cloudflare bot check,
# newest first.  Older fingerprints (chrome131 and below) are rejected.
IMPERSONATE_TARGETS = ('chrome146', 'chrome145', 'chrome142', 'chrome136')


def resolve_impersonate():
    supported = {member.name.lower() for member in BrowserType}
    for target in IMPERSONATE_TARGETS:
        if target in supported:
            return target
    raise RuntimeError(f'No supported impersonation target among {IMPERSONATE_TARGETS}')


class CurlCffiResponse:
    '''Minimal shim translating a curl_cffi response to the requests API.'''

    def __init__(self, response):
        self._response = response

    @property
    def status_code(self):
        return self._response.status_code

    @property
    def content(self):
        return self._response.content

    @property
    def text(self):
        return self._response.text

    def json(self, **kwargs):
        return self._response.json(**kwargs)

    def raise_for_status(self):
        if self._response.status_code >= 400:
            raise requests.exceptions.HTTPError(
                f'{self._response.status_code} Error for {self._response.url}',
                response=self,
            )


class CurlCffiSession:
    '''Context-manager session backed by curl-impersonate (via curl_cffi).

    Wraps the small subset of the requests.Session API used by the views and
    converts curl_cffi failures into requests exceptions so callers keep their
    existing error handling.
    '''

    def __init__(self, impersonate=None, proxies=None):
        self._session = curl_requests.Session(impersonate=impersonate or resolve_impersonate(), proxies=proxies)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()
        return False

    def close(self):
        self._session.close()

    def request(self, method, url, **kwargs):
        kwargs.setdefault('timeout', 10)
        try:
            response = self._session.request(method, url, **kwargs)
        except Exception as exc:
            raise requests.exceptions.RequestException(str(exc)) from exc
        return CurlCffiResponse(response)

    def get(self, url, **kwargs):
        return self.request('GET', url, **kwargs)

    def post(self, url, data=None, **kwargs):
        return self.request('POST', url, data=data, **kwargs)


class CurlCffiService(Service):
    db_transaction = False

    def process(self, service=None):
        proxy = ProxySocks5Service().process(service)
        proxies = {'http': proxy, 'https': proxy} if proxy else None
        return CurlCffiSession(proxies=proxies)
