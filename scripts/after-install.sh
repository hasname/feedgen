#!/bin/bash

pkill uwsgi
LANG=en_US.UTF-8 ~/.pyenv/shims/uwsgi --ini /srv/feedgen.hasname.com/uwsgi.ini > /dev/null 2>&1 &
