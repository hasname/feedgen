#!/bin/bash

~/.pyenv/shims/poetry install
pkill -INT uwsgi
LANG=en_US.UTF-8 ~/.pyenv/shims/poetry run uwsgi --ini /srv/feedgen.hasname.com/uwsgi.ini > /dev/null 2>&1 &
