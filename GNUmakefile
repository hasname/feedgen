#
-include GNUmakefile.local

#
.DEFAULT_GOAL:=		rundev
.PHONY:			.env build rundev test

.env::
	test $(shell wc -l .env | cut -d ' ' -f 1) -eq $(shell wc -l .env.sample | cut -d ' ' -f 1)

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

run::
	pkill -QUIT uwsgi; sleep 1; uv run uwsgi --ini uwsgi.ini > /dev/null 2>&1 &

rundev::
	uv run ./manage.py runserver --settings=feedgen_hasname.settings_dev

test::
	uv run coverage run --source=. ./manage.py test --settings=feedgen_hasname.settings_test
