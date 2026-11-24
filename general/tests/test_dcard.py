import copy
import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import lxml.etree
import requests_mock
from django.conf import settings
from django.core.cache import cache
from django.test import SimpleTestCase, override_settings

from feedgen_hasname import settings as project_settings
from general import services


class DcardTestCase(SimpleTestCase):
    base = 'https://www.dcard.tw'
    paging = f'{base}/service/api/v2/globalPaging'

    def setUp(self):
        self.ns = {'atom': 'http://www.w3.org/2005/Atom', 'xhtml': 'http://www.w3.org/1999/xhtml'}
        self.enterContext(override_settings(CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': self.id(),
                'KEY_PREFIX': 'feedgen_hasname-test',
            },
        }))
        cache.clear()
        self.enterContext(patch.dict(os.environ, {
            'FEEDGEN_DCARD_PROXY': 'socks5h://dcard.proxy.test:1080',
        }, clear=True))
        # Keep HTTP and parsing real while requests_mock replaces the network.
        self.enterContext(patch.object(services, 'CfsolveService', services.RequestsService))
        directory = Path(__file__).parent
        self.markup = {
            name: (directory / f'html_dcard_{name}_app.txt').read_text()
            for name in ('board', 'main')
        }
        self.page = json.loads((directory / 'json_dcard_widgets.json').read_text())

    def configure(self, mock, name='board', page=None):
        path = '/f/mood' if name == 'board' else '/f'
        mock.get(self.base + path, text=self.markup[name])
        mock.get(self.paging + '/head', json={'head': 'fixture-page'})
        mock.get(self.paging + '/page', json=self.page if page is None else page)
        return '/dcard/board/mood' if name == 'board' else '/dcard/main'

    def entries(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertEqual({part.strip() for part in response['Cache-Control'].split(',')}, {'max-age=300', 'public'})
        return lxml.etree.fromstring(response.content).findall('atom:entry', self.ns)

    @requests_mock.mock()
    def test_board_and_main_follow_page_configuration_and_preserve_post_order(self, mock):
        for name, list_key, title in (
            ('board', 'f_popular_v3_75a726e6-d4e3-4902-a410-2430a39fffcb', 'First <post> & "title"'),
            ('main', 'popular_TW_decay_cap', '[心情] First <post> & "title"'),
        ):
            with self.subTest(name=name):
                route = self.configure(mock, name)
                entries = self.entries(self.client.get(route))
                self.assertEqual([entry.findtext('atom:id', namespaces=self.ns) for entry in entries], [
                    f'{self.base}/f/mood/p/240000001', f'{self.base}/f/mood/p/240000002',
                ])
                self.assertEqual(entries[0].findtext('atom:title', namespaces=self.ns), title)
                for entry in entries:
                    self.assertEqual(entry.find('atom:link', self.ns).get('href'),
                                     entry.findtext('atom:id', namespaces=self.ns))
                history = mock.request_history[-3:]
                self.assertEqual([urlsplit(request.url).path for request in history[1:]], [
                    '/service/api/v2/globalPaging/head', '/service/api/v2/globalPaging/page',
                ])
                for request in history:
                    self.assertEqual(request.proxies['https'], 'socks5h://dcard.proxy.test:1080')
                for request in history[1:]:
                    params = parse_qs(urlsplit(request.url).query)
                    self.assertEqual(params['listKey'], [list_key])
                    self.assertEqual(params['enrich'], ['true'])
                    self.assertEqual(params['pinnedPosts'], ['widget'])
                    self.assertEqual(params['platform'], ['mobileweb'])
                self.assertEqual(params['pageKey'], ['fixture-page'])
                self.assertEqual(params['offset'], ['0'])
                self.assertEqual(params['lang'], ['en-US'])

    @requests_mock.mock()
    def test_content_is_escaped_and_only_image_media_are_embedded(self, mock):
        entries = self.entries(self.client.get(self.configure(mock)))
        content = entries[0].find('atom:content', self.ns)
        self.assertEqual(content.get('type'), 'xhtml')
        self.assertEqual(content.find('.//xhtml:p', self.ns).text, 'A <script>alert(1)</script> & B')
        self.assertFalse(content.findall('.//xhtml:script', self.ns))
        image = content.find('.//xhtml:img', self.ns)
        self.assertEqual(image.get('alt'), 'First <post> & "title"')
        self.assertEqual(image.get('src'), 'https://megapx-assets.dcard.tw/images/test/full.jpeg?x=1&y=2')
        self.assertIsNone(entries[1].find('.//xhtml:img', self.ns))

    @requests_mock.mock()
    def test_list_and_page_keys_are_encoded_as_query_parameters(self, mock):
        # The tab configuration is streamed across two scripts in this fixture.
        self.markup['board'] = self.markup['board'].replace(
            'f_popular_v3_75a726e6-d4e3-4902-a410-2430a39fffcb', 'new/list & value',
        )
        route = self.configure(mock)
        mock.get(self.paging + '/head', json={'head': 'page/?&=value'})
        self.entries(self.client.get(route))
        params = parse_qs(urlsplit(mock.last_request.url).query)
        self.assertEqual(params['listKey'], ['new/list & value'])
        self.assertEqual(params['pageKey'], ['page/?&=value'])

    @requests_mock.mock()
    def test_upstream_errors_and_schema_changes_return_uncacheable_503(self, mock):
        missing_title = copy.deepcopy(self.page)
        del missing_title['widgets'][1]['forumList']['items'][0]['post']['title']
        cases = (
            ('/f', {'status_code': 403}),
            ('/f', {'text': '<html><main></main></html>'}),
            ('/f', {'text': '<script>self.__next_f.push([1,"broken"])</script>'}),
            ('/service/api/v2/globalPaging/head', {'status_code': 403}),
            ('/service/api/v2/globalPaging/head', {'text': '<html></html>'}),
            ('/service/api/v2/globalPaging/head', {'json': {}}),
            ('/service/api/v2/globalPaging/head', {'json': {'head': ''}}),
            ('/service/api/v2/globalPaging/page', {'status_code': 503}),
            ('/service/api/v2/globalPaging/page', {'text': '<html></html>'}),
            ('/service/api/v2/globalPaging/page', {'json': {'items': []}}),
            ('/service/api/v2/globalPaging/page', {'json': {'widgets': {}}}),
            ('/service/api/v2/globalPaging/page', {'json': {'widgets': [{'unknownLayout': {}}]}}),
            ('/service/api/v2/globalPaging/page', {'json': missing_title}),
        )
        for path, response in cases:
            with self.subTest(path=path, response=response):
                route = self.configure(mock, 'main')
                mock.get(self.base + path, **response)
                with self.assertLogs('general.views.dcard'):
                    result = self.client.get(route)
                self.assertEqual(result.status_code, 503)
                self.assertEqual(result['Cache-Control'], 'no-store')

    @requests_mock.mock()
    def test_explicitly_empty_api_page_returns_empty_feed(self, mock):
        route = self.configure(mock, page={'widgets': []})
        self.assertEqual(self.entries(self.client.get(route)), [])

    def test_solver_unavailable_returns_uncacheable_503(self):
        with patch.object(services.CfsolveService, 'process', side_effect=OSError('cfsolve unavailable')):
            for route in ('/dcard/board/mood', '/dcard/main'):
                with self.subTest(route=route), self.assertLogs('general.views.dcard'):
                    response = self.client.get(route)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response['Cache-Control'], 'no-store')

    @requests_mock.mock()
    def test_successful_feeds_are_reused_without_starting_solver_session(self, mock):
        for name in ('board', 'main'):
            with self.subTest(name=name):
                route = self.configure(mock, name)
                first = self.client.get(route)
                self.entries(first)
                request_count = mock.call_count
                with patch.object(services.CfsolveService, 'process', side_effect=AssertionError('cache miss')) as process:
                    second = self.client.get(route)
                self.assertEqual(second.status_code, 200)
                self.assertEqual(second.content, first.content)
                process.assert_not_called()
                self.assertEqual(mock.call_count, request_count)

    @requests_mock.mock()
    def test_boards_and_main_have_separate_cache_entries(self, mock):
        routes = [self.configure(mock), self.configure(mock, 'main'), '/dcard/board/relationship']
        mock.get(self.base + '/f/relationship', text=self.markup['board'])
        contents = []
        for route in routes:
            response = self.client.get(route)
            self.entries(response)
            contents.append(response.content)
        self.assertEqual(mock.call_count, 9)
        self.assertEqual(len(set(contents)), 3)
        for route, content in zip(routes, contents, strict=True):
            self.assertEqual(self.client.get(route).content, content)
        self.assertEqual(mock.call_count, 9)

    @requests_mock.mock()
    def test_cached_feed_expires_after_300_seconds(self, mock):
        route = self.configure(mock)
        with patch('django.core.cache.backends.locmem.time.time', return_value=time.time()) as clock:
            self.entries(self.client.get(route))
            clock.return_value += 299
            self.entries(self.client.get(route))
            self.assertEqual(mock.call_count, 3)
            clock.return_value += 2
            self.entries(self.client.get(route))
            self.assertEqual(mock.call_count, 6)

    @requests_mock.mock()
    def test_failed_feed_is_retried_and_success_can_be_cached(self, mock):
        route = self.configure(mock)
        mock.get(self.paging + '/head', status_code=503)
        for _ in range(2):
            with self.assertLogs('general.views.dcard'):
                response = self.client.get(route)
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response['Cache-Control'], 'no-store')
        self.assertEqual(mock.call_count, 4)
        mock.get(self.paging + '/head', json={'head': 'fixture-page'})
        self.entries(self.client.get(route))
        self.entries(self.client.get(route))
        self.assertEqual(mock.call_count, 7)

    @requests_mock.mock()
    def test_cache_prefix_isolates_applications_sharing_storage(self, mock):
        route = self.configure(mock)
        self.entries(self.client.get(route))
        original_key = cache.make_key('same-key')
        other_config = copy.deepcopy(settings.CACHES)
        other_config['default']['KEY_PREFIX'] = 'other-application'
        with override_settings(CACHES=other_config):
            self.assertNotEqual(cache.make_key('same-key'), original_key)
            self.entries(self.client.get(route))
            self.assertEqual(mock.call_count, 6)
        self.entries(self.client.get(route))
        self.assertEqual(mock.call_count, 6)

    @requests_mock.mock()
    def test_unavailable_memcached_falls_back_to_fetching(self, mock):
        route = self.configure(mock)
        config = copy.deepcopy(project_settings.CACHES)
        with tempfile.TemporaryDirectory() as directory:
            config['default']['LOCATION'] = f'unix:{directory}/missing.sock'
            with override_settings(CACHES=config):
                self.entries(self.client.get(route))
                self.entries(self.client.get(route))
                self.assertEqual(mock.call_count, 6)
