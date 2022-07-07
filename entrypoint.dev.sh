#!/bin/sh
exec poetry run ./manage.py runserver --settings=feedgen_hasname.settings_dev
