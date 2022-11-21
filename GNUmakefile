#
-include GNUmakefile.local

#
.DEFAULT_GOAL:=		rundev
.PHONY:			.env build dependency rundev test

.env::
	test $(shell wc -l .env | cut -d ' ' -f 1) -eq $(shell wc -l .env.sample | cut -d ' ' -f 1)

clean::
	rm -f .coverage .dev.sqlite3 db.sqlite3

dependency::
	poetry install

rundev:: dependency
	poetry run ./manage.py runserver --settings=feedgen_hasname.settings_dev

test:: dependency
	poetry run coverage run --source=. ./manage.py test --settings=feedgen_hasname.settings_test
