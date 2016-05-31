#
# Makefile for docker image building and release management
#
REV=$(shell git describe --tags)
REPO=docker.ternaris.com/bagbunker/bagbunker
PUSH_REPO=localhost:5001/bagbunker/bagbunker
IMG=bagbunker:$(REV)


current-revision:
ifeq ($(shell docker inspect $(IMG) 2>/dev/null),[])
	docker build -t $(IMG) .
	@echo "Image built: $(IMG)"
else
	@echo "Image already built: $(IMG)"
endif


develop: current-revision
	cut -d/ -f3 <.git/HEAD |grep '^develop' || (echo; echo "NOT ON DEVELOP BRANCH"; echo; exit 1)
	docker tag $(IMG) $(REPO):develop
	@echo "IMAGE: $(REPO):develop"


staging: current-revision
	cut -d/ -f3 <.git/HEAD |grep '^release-' || (echo; echo "NOT ON RELEASE BRANCH"; echo; exit 1)
	docker tag $(IMG) $(REPO):staging
	@echo "IMAGE: $(REPO):staging"


latest: current-revision
	cut -d/ -f3 <.git/HEAD |grep '^master' || (echo; echo "NOT ON MASTER BRANCH"; echo; exit 1)
	docker tag $(IMG) $(REPO):latest
	@echo "IMAGE: $(REPO):latest"


push-develop:
push-staging:
push-latest:
push-%: %
	docker tag $(REPO):$< $(PUSH_REPO):$<
	docker push $(PUSH_REPO):$<


list-hashes:
	docker inspect docker.ternaris.com/bagbunker/bagbunker:develop |grep -m1 Image || true
	docker inspect docker.ternaris.com/bagbunker/bagbunker:latest |grep -m1 Image || true
	docker inspect docker.ternaris.com/bagbunker/bagbunker:staging |grep -m1 Image || true
