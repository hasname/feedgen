#
.DEFAULT_GOAL:=		rundev
.PHONY:			.env clean dependency deploy rundev test test.ci

.env:
	test $(shell wc -l .env | cut -d ' ' -f 1) -eq $(shell wc -l .env.sample | cut -d ' ' -f 1)

clean:
	rm -f .coverage .dev.sqlite3 general/migrations/0001_initial.py

dependency:
	poetry install

deploy: .env dependency
	cd ansible; ansible-playbook feedgen-hasname.yml

rundev: dependency
	poetry run ./manage.py runserver --settings=feedgen_hasname.settings_dev

test.ci: dependency.ci
	poetry run coverage run --source=. ./manage.py test --settings=feedgen_hasname.settings_test
