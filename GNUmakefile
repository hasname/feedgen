#
-include GNUmakefile.local

#
APPLICATION_NAME?=	feedgen
AWS_PROFILE?=		default
AWS_REGION?=		us-east-1
S3_BUCKET?=		"gslin-codedeploy-us-east-1-${APPLICATION_NAME}"

#
GIT_BRANCH!=		git rev-parse --abbrev-ref HEAD
GIT_DIRTY!=		git diff-files --quiet; echo $$?
GIT_HASH!=		git rev-parse HEAD

#
NOW!=			date -u +%Y%m%d-%H%M%S
S3_KEY=			${APPLICATION_NAME}/${GIT_BRANCH}-${NOW}-${GIT_HASH}

#
.DEFAULT_GOAL:=		test
.PHONY:			deploy deploy-force force-deploy push test _git_dirty

#
deploy: _git_dirty deploy-force
	@true

deploy-force:
	aws deploy push \
		--application-name "${APPLICATION_NAME}" \
		--profile "${AWS_PROFILE}" \
		--region "${AWS_REGION}" \
		--s3-location "s3://${S3_BUCKET}/${S3_KEY}"
	aws deploy create-deployment \
		--application-name "${APPLICATION_NAME}" \
		--deployment-group-name "${GIT_BRANCH}" \
		--profile "${AWS_PROFILE}" \
		--region "${AWS_REGION}" \
		--s3-location bucket="${S3_BUCKET},key=${S3_KEY},bundleType=zip"

force-deploy: deploy-force
	@true

push:
	git push -v origin master

test:
	nosetests --no-byte-compile

_git_dirty:
ifneq (${GIT_DIRTY}, 0)
	$(error 'Git is dirty, stop deploying.')
endif
