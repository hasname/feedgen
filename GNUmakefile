#
.DEFAULT_GOAL:=		test
.PHONY:			clean deploy push test

clean:
	rm -fr feedgen_hasname.egg-info/

deploy:
	ansible-playbook -i ansible/hosts ansible/feedgen.yml

push:
	git push -v origin master

test:
	nosetests --cover-package feedgen_hasname --no-byte-compile --with-coverage
