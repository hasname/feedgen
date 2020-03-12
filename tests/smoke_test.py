#!/usr/bin/env python3

import bottle
import feedgen_hasname

class SmokeTest(object):
    def setup():
        self.app = feedgen_hasname.FeedgenHasname()

    def test_index():
        try:
            self.app.index()
        except bottle.HTTPResponse:
            assert True
            return

        assert False

    def test_robotstxt():
        self.app.robotstxt()
