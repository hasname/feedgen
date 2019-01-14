#
.DEFAULT_GOAL:=		test

deploy:
	ansible-playbook feedgen.yml

push:
	git push -v origin master

test:
	nosetests --cover-package feedgen_hasname --no-byte-compile --with-coverage
