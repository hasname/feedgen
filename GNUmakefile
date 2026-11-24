#
-include GNUmakefile.local

#
.DEFAULT_GOAL:=		rundev
.PHONY:			.env cfsolve ci clean deploy lint quality run rundev test

.env::
	test $(shell wc -l .env | cut -d ' ' -f 1) -eq $(shell wc -l .env.sample | cut -d ' ' -f 1)

ci:: lint quality test
	@true

CFSOLVE_SOURCE_DIR ?= .cfsolve

cfsolve::
	bash scripts/install-cfsolve.sh "$(CFSOLVE_SOURCE_DIR)"

clean::
	rm -f .coverage .dev.sqlite3 db.sqlite3

DEPLOY_DEST = ${DEPLOY_USER}@${DEPLOY_HOST}:~${DEPLOY_USER}/feedgen/

deploy::
ifndef DEPLOY_HOST
	$(error $$DEPLOY_HOST is not defined in GNUmakefile.local)
endif
ifndef DEPLOY_USER
	$(error $$DEPLOY_USER is not defined in GNUmakefile.local)
endif
	bash scripts/install-cfsolve.sh "$(CFSOLVE_SOURCE_DIR)"
	rsync \
		-Favz \
		--delete-after \
		--exclude-from=.gitignore \
		./ \
		${DEPLOY_DEST}
	rsync -avzR -- \
		"$(CFSOLVE_SOURCE_DIR)/./target/release/challenge" \
		"$(CFSOLVE_SOURCE_DIR)/./profiles/safari-26-ios.json" \
		"$(CFSOLVE_SOURCE_DIR)/./profiles/safari-26-ios/answers.json" \
		"$(CFSOLVE_SOURCE_DIR)/./profiles/safari-26-ios/challenge-page-answers.json" \
		"$(CFSOLVE_SOURCE_DIR)/./LICENSE" \
		${DEPLOY_DEST}.cfsolve-upload/
	ssh ${DEPLOY_USER}@${DEPLOY_HOST} 'bash -lc "cd ~/feedgen && bash scripts/activate-cfsolve.sh"'
	rsync -aL --checksum --chmod=600 --ignore-missing-args .env ${DEPLOY_DEST}
	ssh ${DEPLOY_USER}@${DEPLOY_HOST} 'bash -lc "cd ~/feedgen && uv sync --frozen"'
	ssh ${DEPLOY_USER}@${DEPLOY_HOST} "install -D -m 0644 ~/feedgen/feedgen.service ~/.config/systemd/user/feedgen.service && systemctl --user daemon-reload && systemctl --user reenable feedgen.service"
	ssh ${DEPLOY_USER}@${DEPLOY_HOST} "systemctl --user restart feedgen.service && sleep 3 && systemctl --user is-active feedgen.service"

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
