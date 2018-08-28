#!/usr/bin/env python3

import bottle
import feedgen_hasname

def test_index():
    try:
        feedgen_hasname.index()
    except bottle.HTTPResponse:
        assert True
        return

    assert False

def test_robotstxt():
    feedgen_hasname.robotstxt()
