import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import requests
from curl_cffi import requests as curl_requests
from django.test import SimpleTestCase

from general.services import CfsolveService


class CfsolveServiceTestCase(SimpleTestCase):
    url = 'https://www.dcard.tw/service/api/v2/popularForums/GetHead?listKey=popularForums'
    user_agent = 'profile-user-agent'

    def setUp(self):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        self.profile = Path(directory) / 'profile.json'
        self.profile.write_text(json.dumps({
            'transport': {'headers': {'User-Agent': self.user_agent}},
        }), encoding='utf-8')
        self.enterContext(patch.dict(os.environ, {
            'FEEDGEN_CFSOLVE_BINARY': '/test/challenge',
            'FEEDGEN_CFSOLVE_PROFILE': str(self.profile),
            'FEEDGEN_CFSOLVE_ATTEMPTS': '2',
            'FEEDGEN_CFSOLVE_TIMEOUT': '5',
        }, clear=True))
        self.run = self.enterContext(patch('general.services.cfsolve_service.subprocess.run'))
        self.run.return_value = subprocess.CompletedProcess([], 0, 'cf_clearance=clearance-1\n', '')
        self.calls = []
        self.responses = [self.response()]

        def request(session, method, url, **kwargs):
            self.calls.append({
                **kwargs, 'method': method, 'url': url,
                'cookies': list(session.cookies.jar), 'trust_env': session.trust_env,
            })
            response = self.responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response

        self.enterContext(patch.object(curl_requests.Session, 'request', request))

    def response(self, status=200, challenged=False, url=None):
        response = requests.Response()
        response.status_code = status
        response.url = url or self.url
        response._content = b'{}'
        if challenged:
            response.headers['cf-mitigated'] = 'challenge'
        return response

    def challenge(self):
        return self.response(403, challenged=True)

    def test_success_and_ordinary_errors_skip_solver(self):
        for status in (200, 403, 404, 429, 503):
            with self.subTest(status=status), CfsolveService().process('dcard') as session:
                self.responses = [self.response(status)]
                response = session.get(self.url)
                self.assertEqual(response.status_code, status)
                if status >= 400:
                    with self.assertRaises(requests.exceptions.HTTPError):
                        response.raise_for_status()
        self.run.assert_not_called()

    def test_clearance_is_reused_and_scoped_to_host(self):
        self.responses = [self.challenge(), self.response(), self.response()]
        headers = {'user-agent': 'caller-agent', 'Accept': 'application/json'}
        with CfsolveService().process('dcard') as session:
            self.assertEqual(session._session.impersonate, 'safari260_ios')
            session.get(self.url, headers=headers)
            session.get('https://www.dcard.tw/service/api/v2/popularForums/GetPage?pageKey=test')
        self.run.assert_called_once()
        command = self.run.call_args.args[0]
        self.assertEqual(command[:3], ['/test/challenge', '--page', self.url])
        self.assertEqual(command[4:], ['--solve', '--fingerprint', str(self.profile)])
        self.assertFalse(Path(command[3]).exists())
        self.assertEqual(self.run.call_args.kwargs['timeout'], 5)
        self.assertEqual(headers['user-agent'], 'caller-agent')
        for call in self.calls:
            self.assertEqual(call['headers']['User-Agent'], self.user_agent)
            self.assertEqual(call['timeout'], 10)
            self.assertFalse(call['trust_env'])
        self.assertEqual(self.calls[0]['cookies'], [])
        for call in self.calls[1:]:
            cookie, = call['cookies']
            self.assertEqual((cookie.name, cookie.value, cookie.domain),
                             ('cf_clearance', 'clearance-1', 'www.dcard.tw'))
            self.assertTrue(cookie.secure)

    def test_rejected_clearance_is_replaced(self):
        self.responses = [self.challenge(), self.challenge(), self.response()]
        self.run.side_effect = [
            subprocess.CompletedProcess([], 0, 'cf_clearance=old\n', ''),
            subprocess.CompletedProcess([], 0, 'cf_clearance=new\n', ''),
        ]
        with CfsolveService().process('dcard') as session:
            self.assertEqual(session.get(self.url).status_code, 200)
        self.assertEqual(self.run.call_count, 2)
        self.assertEqual([cookie.value for cookie in self.calls[-1]['cookies']], ['new'])

    def test_persistent_challenge_has_bounded_retries(self):
        # Cloudflare may return a challenge even with HTTP 200.
        self.responses = [self.response(200, challenged=True) for _ in range(3)]
        with CfsolveService().process('dcard') as session, self.assertRaises(requests.exceptions.HTTPError):
            session.get(self.url)
        self.assertEqual(self.run.call_count, 2)
        self.assertEqual(len(self.calls), 3)

    def test_solver_failure_and_timeout_clean_up_and_stop(self):
        failures = (
            subprocess.CompletedProcess([], 1, 'cf_clearance=invalid\n', 'private diagnostic'),
            subprocess.CompletedProcess([], 0, 'turnstile-token\n', ''),
            subprocess.TimeoutExpired(['challenge', '--proxy', 'private-proxy'], 5),
        )
        for failure in failures:
            with self.subTest(failure=type(failure).__name__):
                self.run.reset_mock(side_effect=True)
                self.run.side_effect = [failure, failure]
                self.responses = [self.challenge()]
                with CfsolveService().process('dcard') as session, self.assertLogs() as logs:
                    with self.assertRaises(requests.exceptions.HTTPError):
                        session.get(self.url)
                    self.assertFalse(session._session.cookies)
                self.assertEqual(self.run.call_count, 2)
                directories = [call.args[0][3] for call in self.run.call_args_list]
                self.assertEqual(len(set(directories)), 2)
                self.assertTrue(all(not Path(path).exists() for path in directories))
                self.assertNotIn('private', ' '.join(logs.output))

    def test_missing_binary_and_network_errors_use_requests_exceptions(self):
        self.responses = [self.challenge()]
        self.run.side_effect = FileNotFoundError('challenge')
        with (
            CfsolveService().process('dcard') as session,
            self.assertRaisesMessage(requests.exceptions.RequestException, 'Cannot execute cfsolve'),
        ):
            session.get(self.url)
        self.assertEqual(self.run.call_count, 1)
        self.assertFalse(Path(self.run.call_args.args[0][3]).exists())
        self.run.reset_mock(side_effect=True)
        self.responses = [curl_requests.exceptions.RequestException('connection failed')]
        with CfsolveService().process('dcard') as session, self.assertRaises(requests.exceptions.RequestException):
            session.get(self.url)
        self.run.assert_not_called()

    def test_proxy_is_shared_with_solver(self):
        default = 'socks5h://default.proxy:1080'
        explicit = 'http://user:password@custom.proxy:8080'
        environment = 'http://environment.proxy:3128'
        cases = (
            ({}, None),
            ({'FEEDGEN_HTTP_PROXY': default}, default),
            ({'FEEDGEN_HTTP_PROXY': default, 'FEEDGEN_DCARD_PROXY': ''}, default),
            ({'FEEDGEN_DCARD_PROXY': explicit, 'HTTPS_PROXY': environment, 'NO_PROXY': '*'}, explicit),
            ({'HTTPS_PROXY': environment}, environment),
            ({'ALL_PROXY': environment}, environment),
            ({'HTTPS_PROXY': environment, 'NO_PROXY': 'www.dcard.tw'}, None),
        )
        for env, expected in cases:
            with self.subTest(env=env), patch.dict(os.environ, env):
                self.responses = [self.challenge(), self.response()]
                with CfsolveService().process('dcard') as session:
                    session.get(self.url)
                command = self.run.call_args.args[0]
                if expected:
                    self.assertEqual(command[-2:], ['--proxy', expected])
                else:
                    self.assertNotIn('--proxy', command)
                proxies = {'http': expected, 'https': expected} if expected else {}
                for call in self.calls[-2:]:
                    self.assertEqual(call['proxies'], proxies)
                self.assertFalse(any(key.lower() in ('http_proxy', 'https_proxy', 'all_proxy', 'no_proxy')
                                     for key in self.run.call_args.kwargs['env']))

    def test_dataimpulse_sticky_session_preserves_credentials(self):
        cases = (
            ('login', 'login__sessid.generated'),
            ('login__cr.tw', 'login__cr.tw;sessid.generated'),
            ('login__sessid.existing', 'login__sessid.existing'),
            ('login__cr.tw;sessid.existing', 'login__cr.tw;sessid.existing'),
            ('login__cr.tw%3Bsessid.existing', 'login__cr.tw%3Bsessid.existing'),
        )
        for username, expected_username in cases:
            proxy = f'socks5h://{username}:p%40ss%3Aword@gw.dataimpulse.com:824'
            expected = f'socks5h://{expected_username}:p%40ss%3Aword@gw.dataimpulse.com:824'
            with self.subTest(username=username), patch.dict(os.environ, FEEDGEN_DCARD_PROXY=proxy):
                with patch('general.services.cfsolve_service.secrets.token_hex', return_value='generated'):
                    self.responses = [self.challenge(), self.response(), self.response()]
                    with CfsolveService().process('dcard') as session:
                        session.get(self.url)
                        session.get(self.url)
                self.assertEqual(self.run.call_args.args[0][-1], expected)
                for call in self.calls[-3:]:
                    self.assertEqual(call['proxies'], {'http': expected, 'https': expected})

    def test_impersonate_uses_single_service_target_and_ignores_global(self):
        os.environ['FEEDGEN_IMPERSONATE'] = 'chrome136,chrome150'
        with CfsolveService().process('dcard') as session:
            self.assertEqual(session._session.impersonate, 'safari260_ios')
        os.environ['FEEDGEN_DCARD_IMPERSONATE'] = 'safari270_ios'
        with CfsolveService().process('dcard') as session:
            self.assertEqual(session._session.impersonate, 'safari270_ios')
        os.environ['FEEDGEN_DCARD_IMPERSONATE'] = 'chrome146,chrome150'
        with self.assertRaisesMessage(ValueError, 'one impersonate target'):
            CfsolveService().process('dcard')

    def test_invalid_profile_and_limits_fail_before_network(self):
        for contents in ('{}', 'not json', '{"transport": {"headers": {"User-Agent": null}}}'):
            with self.subTest(contents=contents):
                self.profile.write_text(contents, encoding='utf-8')
                with self.assertRaises(requests.exceptions.RequestException):
                    CfsolveService().process('dcard')
        for key in ('FEEDGEN_CFSOLVE_ATTEMPTS', 'FEEDGEN_CFSOLVE_TIMEOUT'):
            with self.subTest(key=key), patch.dict(os.environ, {key: '0'}), self.assertRaises(ValueError):
                CfsolveService().process('dcard')
        self.assertEqual(self.calls, [])
        self.run.assert_not_called()
