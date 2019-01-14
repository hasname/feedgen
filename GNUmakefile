#
.DEFAULT_GOAL:=		test

push:
	git push -v origin master

test:
	nosetests --cover-package feedgen_hasname --no-byte-compile --with-coverage
