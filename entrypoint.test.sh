#!/bin/sh
exec poetry run coverage run --source=. ./manage.py test --settings=feedgen_hasname.settings_test
