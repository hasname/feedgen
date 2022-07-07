#!/bin/sh
exec poetry run ./manage.py runserver --noreload --settings=feedgen_hasname.settings_dev
