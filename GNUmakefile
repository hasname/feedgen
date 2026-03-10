#
-include GNUmakefile.local

#
.DEFAULT_GOAL:=		rundev
.PHONY:			.env build ci lint quality rundev test

.env::
	test $(shell wc -l .env | cut -d ' ' -f 1) -eq $(shell wc -l .env.sample | cut -d ' ' -f 1)

ci:: lint quality test
	@true

clean::
	rm -f .coverage .dev.sqlite3 db.sqlite3

deploy::
ifndef DEPLOY_HOST
	$(error $$DEPLOY_HOST is not defined in GNUmakefile.local)
endif
ifndef DEPLOY_USER
	$(error $$DEPLOY_USER is not defined in GNUmakefile.local)
endif
	rsync \
		-Favz \
		--delete-after \
		--exclude-from=.gitignore \
		./ \
		${DEPLOY_USER}@${DEPLOY_HOST}:~${DEPLOY_USER}/feedgen/
	ssh ${DEPLOY_USER}@${DEPLOY_HOST} "systemctl --user restart feedgen.service"

lint::
	uv run ruff check .

quality::
	uv run radon cc -s .
	uv run radon cc --json . | uv run python -c 'import json,sys;d=json.load(sys.stdin);b=[(f,x["name"],x["lineno"],x["complexity"]) for f,bs in d.items() for x in bs if x["complexity"]>50];[print(f"{f}:{l} {n} (complexity: {c})") for f,n,l,c in b];sys.exit(1 if b else 0)'

run::
	pkill -QUIT uwsgi; sleep 1; uv run uwsgi --ini uwsgi.ini > /dev/null 2>&1 &

rundev::
	uv run ./manage.py runserver --settings=feedgen_hasname.settings_dev

test::
	uv run coverage run --source=. ./manage.py test --settings=feedgen_hasname.settings_test
