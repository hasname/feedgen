#
.DEFAULT_GOAL:=		rundev
.PHONY:			.env build dependency.ci deploy rundev test test.ci

.env:
	test $(shell wc -l .env | cut -d ' ' -f 1) -eq $(shell wc -l .env.sample | cut -d ' ' -f 1)

build:
	docker build -t feedgen_hasname .

dependency.ci:
	poetry install

deploy: .env dependency
	cd ansible; ansible-playbook feedgen-hasname.yml

rundev: build
	docker run -t -p 127.0.0.1:8000:8000/tcp --entrypoint ./entrypoint.dev.sh feedgen_hasname

test: build
	docker run --entrypoint ./entrypoint.test.sh feedgen_hasname

test.ci: dependency.ci
	poetry run coverage run --source=. ./manage.py test --settings=feedgen_hasname.settings_test
