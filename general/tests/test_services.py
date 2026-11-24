import os
from unittest.mock import MagicMock, patch

import requests_mock
from curl_cffi import requests as curl_requests
from django.test import SimpleTestCase

from general.services import CurlCffiService, RequestsService


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


class CurlCffiServiceTestCase(SimpleTestCase):
    def setUp(self):
        self.enterContext(patch.dict(os.environ, {}, clear=True))

    def test_104_session_randomly_picks_default_impersonate(self):
        for _ in range(20):
            with patch.object(curl_requests, 'Session') as curl_session, CurlCffiService().process('104'):
                self.assertIn(
                    curl_session.call_args.kwargs['impersonate'],
                    {'chrome136', 'chrome146', 'chrome150'},
                )

    def test_impersonate_environment_supports_multiple_targets(self):
        # Service-specific setting wins over the global one; one target is
        # picked at random from the comma-separated list.
        for targets in ('chrome136', 'chrome136,chrome146,chrome150'):
            os.environ.update({'FEEDGEN_IMPERSONATE': 'chrome116', 'FEEDGEN_104_IMPERSONATE': targets})
            expected = set(targets.split(','))
            for _ in range(20):
                with patch.object(curl_requests, 'Session') as curl_session, CurlCffiService().process('104'):
                    self.assertIn(curl_session.call_args.kwargs['impersonate'], expected)

    def test_impersonate_global_environment_falls_back_to_chrome(self):
        # Global setting without a service-specific one applies to any service;
        # unset environment keeps the previous behaviour ('chrome').
        for impersonate_env, expected in (({'FEEDGEN_IMPERSONATE': 'chrome110'}, 'chrome110'), ({}, 'chrome')):
            with (
                self.subTest(impersonate_env=impersonate_env),
                patch.dict(os.environ, impersonate_env),
                patch.object(curl_requests, 'Session') as curl_session,
                CurlCffiService().process('dcard'),
            ):
                self.assertEqual(curl_session.call_args.kwargs['impersonate'], expected)

    def test_104_session_uses_configured_proxy(self):
        default = 'socks5h://default.example:1080'
        override = 'socks5h://104.example:1080'
        for service_proxy, expected in ((override, override), ('', default)):
            with (
                self.subTest(service_proxy=service_proxy),
                patch.dict(os.environ, FEEDGEN_HTTP_PROXY=default, FEEDGEN_104_PROXY=service_proxy),
                patch.object(curl_requests, 'Session') as curl_session,
                CurlCffiService().process('104'),
            ):
                self.assertEqual(curl_session.call_args.kwargs['proxies'], {'http': expected, 'https': expected})

    def test_impersonated_session_sends_fetch_metadata(self):
        captured = {}

        def fake_request(self, method, url, **kwargs):
            captured.update(kwargs, method=method, url=url)
            response = MagicMock(status_code=200, content=b'', text='', url=url)
            response.json.return_value = {}
            return response

        with CurlCffiService().process('104') as session, patch.object(
            curl_requests.Session, 'request', fake_request,
        ):
            session.get('https://www.104.com.tw/jobs/search/api/jobs', headers={'Sec-Fetch-Mode': 'cors'})
            self.assertEqual(captured['headers']['Sec-Fetch-Mode'], 'cors')
            self.assertEqual(captured['timeout'], 10)
