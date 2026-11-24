import json
import logging
import os
import re
import secrets
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

import requests
from service_objects.services import Service

from .curl_cffi_service import DEFAULT_DCARD_IMPERSONATE, CurlCffiSession
from .proxy_socks5_service import ProxySocks5Service

logger = logging.getLogger(__name__)


class CfsolveSession(CurlCffiSession):
    '''Solve Cloudflare challenges and reuse the profile and proxy for requests.'''

    def __init__(self, proxy=None, impersonate=DEFAULT_DCARD_IMPERSONATE):
        self._binary = os.getenv('FEEDGEN_CFSOLVE_BINARY') or 'challenge'
        self._profile = os.getenv('FEEDGEN_CFSOLVE_PROFILE') or 'safari-26-ios.json'
        self._attempts = int(os.getenv('FEEDGEN_CFSOLVE_ATTEMPTS') or '3')
        self._timeout = float(os.getenv('FEEDGEN_CFSOLVE_TIMEOUT') or '300')
        if self._attempts < 1 or self._timeout <= 0:
            raise ValueError('cfsolve attempts and timeout must be positive')
        if ',' in impersonate:
            raise ValueError('cfsolve requires one impersonate target matching its profile')

        try:
            profile = json.loads(Path(self._profile).read_text(encoding='utf-8'))
            self._user_agent = profile['transport']['headers']['User-Agent']
            if not isinstance(self._user_agent, str) or not self._user_agent:
                raise ValueError('Missing User-Agent')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise requests.exceptions.RequestException('Cannot read cfsolve profile User-Agent') from exc

        self._proxy = self._sticky_proxy(proxy) if proxy else None
        self._proxy_resolved = bool(proxy)
        super().__init__(impersonate=impersonate)
        # Resolve environment proxies once and explicitly share the result with
        # cfsolve, including NO_PROXY, so both clients use the same exit IP.
        self._session.trust_env = False

    @staticmethod
    def _sticky_proxy(proxy):
        parsed = urlsplit(proxy)
        if parsed.hostname != 'gw.dataimpulse.com' or not parsed.username:
            return proxy
        username = parsed.username
        if re.search(r'(?:__|;)sessid\.', unquote(username)):
            return proxy
        separator = ';' if '__' in unquote(username) else '__'
        username += f'{separator}sessid.{secrets.token_hex(8)}'
        return parsed._replace(netloc=username + parsed.netloc[len(parsed.username):]).geturl()

    def _solve(self, url):
        # cfsolve writes request/response artifacts; remove them after every run.
        with tempfile.TemporaryDirectory(prefix='cfsolve-') as directory:
            command = [
                self._binary, '--page', url, directory, '--solve',
                '--fingerprint', self._profile,
            ]
            if self._proxy:
                command.extend(['--proxy', self._proxy])
            env = {
                key: value for key, value in os.environ.items()
                if key.lower() not in ('http_proxy', 'https_proxy', 'all_proxy', 'no_proxy')
            }
            try:
                output = subprocess.run(
                    command, capture_output=True, text=True, timeout=self._timeout,
                    check=False, env=env,
                )
            except subprocess.TimeoutExpired:
                logger.warning('cfsolve timed out')
                return False
            except OSError:
                raise requests.exceptions.RequestException('Cannot execute cfsolve binary') from None

        match = re.search(r'^cf_clearance=([^\s;]+)$', output.stdout, re.MULTILINE)
        if output.returncode != 0 or not match:
            # Solver output may contain proxy credentials and cookies.
            logger.warning('cfsolve failed to return a clearance (exit %s)', output.returncode)
            return False
        self._session.cookies.set(
            'cf_clearance', match.group(1), domain=urlsplit(url).hostname,
            secure=urlsplit(url).scheme == 'https',
        )
        return True

    def get(self, url, **kwargs):
        if not self._proxy_resolved:
            proxy = requests.utils.select_proxy(url, requests.utils.get_environ_proxies(url))
            self._proxy = self._sticky_proxy(proxy) if proxy else None
            self._proxy_resolved = True
        kwargs['proxies'] = {'http': self._proxy, 'https': self._proxy} if self._proxy else {}
        headers = requests.structures.CaseInsensitiveDict(kwargs.get('headers') or {})
        headers['User-Agent'] = self._user_agent
        kwargs['headers'] = headers

        response = super().get(url, **kwargs)
        for _ in range(self._attempts):
            if response.headers.get('cf-mitigated') != 'challenge':
                return response
            self._session.cookies.delete('cf_clearance')
            if self._solve(response.url):
                response = super().get(url, **kwargs)
        if response.headers.get('cf-mitigated') == 'challenge':
            raise requests.exceptions.HTTPError('Cloudflare challenge was not cleared', response=response)
        return response


class CfsolveService(Service):
    db_transaction = False

    def process(self, service=None):
        proxy = ProxySocks5Service().process(service)
        # The global/random browser setting may not match the solver profile.
        impersonate = os.getenv(f'FEEDGEN_{service.upper()}_IMPERSONATE') if service else None
        return CfsolveSession(proxy=proxy, impersonate=impersonate or DEFAULT_DCARD_IMPERSONATE)
