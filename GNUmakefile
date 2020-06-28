#
.DEFAULT_GOAL:=		rundev
.PHONY:			clean dependency deploy.production deploy.staging rundev test

clean:
	rm -f .coverage .dev.sqlite3 general/migrations/0001_initial.py

dependency:
	poetry install

deploy.production: dependency
	cd ansible; ansible-playbook feedgen-hasname.yml --limit production

deploy.staging: dependency
	cd ansible; ansible-playbook feedgen-hasname.yml --limit staging

rundev: dependency
	poetry run ./manage.py runserver --settings=feedgen_hasname.settings_dev

test: dependency
	poetry run coverage run --source=. ./manage.py test --settings=feedgen_hasname.settings_test
