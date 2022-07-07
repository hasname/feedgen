#!/bin/sh
exec poetry run uwsgi --ini uwsgi.ini
