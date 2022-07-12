#
-include GNUmakefile.local

#
.DEFAULT_GOAL:=		rundev
.PHONY:			.env build clean dependency.ci rundev test test.ci

.env::
	test $(shell wc -l .env | cut -d ' ' -f 1) -eq $(shell wc -l .env.sample | cut -d ' ' -f 1)

build::
	docker build -t feedgen_hasname .
	docker container prune -f
	docker image prune -f

clean::
	docker container prune -f
	docker image prune -f

rundev:: build
	docker run -t -p 127.0.0.1:8000:8000/tcp --entrypoint ./entrypoint.dev.sh feedgen_hasname

test:: build
	docker run --entrypoint ./entrypoint.test.sh feedgen_hasname

up::
	docker compose --env-file ~/.config/feedgen/.env up -d

# Used by CI
dependency.ci::
	poetry install

test.ci:: dependency.ci
	poetry run coverage run --source=. ./manage.py test --settings=feedgen_hasname.settings_test
