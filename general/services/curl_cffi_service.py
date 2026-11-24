import os
import random

import requests
from curl_cffi import requests as curl_requests
from service_objects.services import Service

from .proxy_socks5_service import ProxySocks5Service

# Cloudflare on 104.com.tw challenges (403 "Just a moment...") the generic
# 'chrome' fingerprint and some specific versions (e.g. chrome152), while
# letting others through. Which versions pass changes over time, so the
# default below sticks to versions known to work recently (verified 2026-11).
# Override via FEEDGEN_104_IMPERSONATE / FEEDGEN_{SERVICE}_IMPERSONATE or the
# global FEEDGEN_IMPERSONATE: comma-separated curl_cffi targets, one of which
# is picked at random per session.
DEFAULT_104_IMPERSONATE = 'chrome136,chrome146,chrome150'

# Pair cfsolve's safari-26-ios profile with curl_cffi's Safari iOS fingerprint.
DEFAULT_DCARD_IMPERSONATE = 'safari260_ios'


class CurlCffiResponse:
    '''Minimal shim translating a curl_cffi response to the requests API.'''

    def __init__(self, response):
        self._response = response

    @property
    def status_code(self):
        return self._response.status_code

    @property
    def headers(self):
        return self._response.headers

    @property
    def url(self):
        return self._response.url

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
        self._session = curl_requests.Session(impersonate=impersonate or 'chrome', proxies=proxies)

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
        env_key = f'FEEDGEN_{service.upper()}_IMPERSONATE' if service else 'FEEDGEN_IMPERSONATE'
        defaults = {'104': DEFAULT_104_IMPERSONATE, 'dcard': DEFAULT_DCARD_IMPERSONATE}
        raw = os.getenv(env_key) or os.getenv('FEEDGEN_IMPERSONATE') or defaults.get(service, '')
        targets = [target.strip() for target in raw.split(',') if target.strip()]
        return CurlCffiSession(impersonate=random.choice(targets) if targets else None, proxies=proxies)
