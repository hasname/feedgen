#
APPLICATION_NAME?=	feedgen
AWS_PROFILE?=		default
AWS_REGION?=		us-east-1
S3_BUCKET?=		"gslin-codedeploy-us-east-1-${APPLICATION_NAME}"

#
.DEFAULT_GOAL:=		test

push:
	git push -v origin master

test:
	nosetests --cover-package feedgen_hasname --no-byte-compile --with-coverage

-include codedeploy-makefile/codedeploy.gnumakefile
