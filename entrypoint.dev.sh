#!/bin/sh
poetry run ./manage.py makemigrations
poetry run ./manage.py migrate
exec poetry run ./manage.py runserver --noreload --settings=feedgen_hasname.settings_dev
