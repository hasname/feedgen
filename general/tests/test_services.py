import os
from unittest.mock import patch

import requests_mock
from django.test import SimpleTestCase

from general.services import RequestsService


class RequestsServiceTestCase(SimpleTestCase):
    def setUp(self):
        self.enterContext(patch.dict(os.environ, {}, clear=True))
        self.http = self.enterContext(requests_mock.Mocker())
        self.http.get(requests_mock.ANY, text='ok')

    def assert_proxy(self, session, proxy):
        for scheme in ('http', 'https'):
            with self.subTest(scheme=scheme):
                session.get(f'{scheme}://example.test/')
                self.assertEqual(self.http.last_request.proxies.get(scheme), proxy)

    def test_unconfigured_session_preserves_defaults(self):
        with RequestsService().process('dcard') as session:
            self.assert_proxy(session, None)
            self.assertEqual(self.http.last_request.headers['User-Agent'], 'feedgen')
            self.assertEqual(self.http.last_request.timeout, 10)

    def test_global_proxy_supports_socks_and_http(self):
        for scheme in ('socks5', 'socks5h', 'http'):
            proxy = f'{scheme}://user:password@proxy.example:1080'
            with self.subTest(scheme=scheme), patch.dict(os.environ, {'FEEDGEN_HTTP_PROXY': proxy}):
                for service in (None, 'dcard', 'bookwalker'):
                    with RequestsService().process(service) as session:
                        self.assert_proxy(session, proxy)

    def test_empty_service_proxy_inherits_default(self):
        proxy = 'socks5h://default.example:1080'
        os.environ.update({'FEEDGEN_HTTP_PROXY': proxy, 'FEEDGEN_DCARD_PROXY': ''})
        with RequestsService().process('dcard') as session:
            self.assert_proxy(session, proxy)

    def test_service_proxies_are_independent_and_override_environment(self):
        default = 'socks5h://default.example:1080'
        dcard = 'socks5h://dcard.example:1080'
        shopee = 'socks5://shopee.example:1080'
        os.environ.update({
            'FEEDGEN_HTTP_PROXY': default,
            'FEEDGEN_DCARD_PROXY': dcard,
            'FEEDGEN_SHOPEE_PROXY': shopee,
            'HTTP_PROXY': 'http://environment.example:3128',
            'HTTPS_PROXY': 'http://environment.example:3128',
        })
        with (
            RequestsService().process('dcard') as dcard_session,
            RequestsService().process('shopee') as shopee_session,
            RequestsService().process('bookwalker') as bookwalker_session,
        ):
            self.assert_proxy(dcard_session, dcard)
            self.assert_proxy(shopee_session, shopee)
            self.assert_proxy(bookwalker_session, default)
            self.assert_proxy(dcard_session, dcard)

    def test_standard_environment_proxy_remains_available(self):
        proxy = 'http://environment.example:3128'
        os.environ.update({
            'FEEDGEN_HTTP_PROXY': '',
            'FEEDGEN_DCARD_PROXY': '',
            'HTTP_PROXY': proxy,
            'HTTPS_PROXY': proxy,
        })
        with RequestsService().process('dcard') as session:
            self.assert_proxy(session, proxy)
            os.environ['NO_PROXY'] = 'example.test'
            self.assert_proxy(session, None)

    def test_explicit_request_options_override_defaults(self):
        os.environ['FEEDGEN_DCARD_PROXY'] = 'socks5h://dcard.example:1080'
        proxies = {'http': 'socks5h://override.example:1080', 'https': 'socks5h://override.example:1080'}
        with RequestsService().process('dcard') as session:
            session.get('https://example.test/', proxies=proxies, timeout=3)
            self.assertEqual(self.http.last_request.proxies, proxies)
            self.assertEqual(self.http.last_request.timeout, 3)
