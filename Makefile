VERSION := $(shell git rev-parse --short HEAD)
ARCH := $(shell uname -m)
UV := ~/.local/bin/uv
CURL := $(shell if command -v axel >/dev/null 2>&1; then echo "axel"; else echo "curl"; fi)
REMOTE := nvidia@gpu
REMOTE_PATH := ~/projects/wxocr
DOCKER_REGISTRY := registry.lazycat.cloud/x/wxocr
DOCKER_NAME := wxocr
ENV_PROXY := http://192.168.1.200:7890

sync-from-gpu:
	rsync -arvzlt --delete --exclude-from=.rsyncignore $(REMOTE):$(REMOTE_PATH)/ ./

sync-to-gpu:
	ssh -t $(REMOTE) "mkdir -p $(REMOTE_PATH)"
	rsync -arvzlt --delete --exclude-from=.rsyncignore ./ $(REMOTE):$(REMOTE_PATH)

sync-clean:
	ssh -t $(REMOTE) "rm -rf $(REMOTE_PATH)"

prepare: sync-to-gpu
	ssh -t $(REMOTE) "cd $(REMOTE_PATH) && \
		export HTTPS_PROXY=$(ENV_PROXY) && \
		export HTTP_PROXY=$(ENV_PROXY) && \
		export ALL_PROXY=$(ENV_PROXY) && \
		export NO_PROXY=localhost,192.168.1.200,registry.lazycat.cloud && \
		$(UV) venv && \
		$(UV) sync

run: sync-to-gpu
	ssh -t $(REMOTE) "cd $(REMOTE_PATH) && \
		$(UV) run main.py

build: compile
	ssh -t $(REMOTE) "cd $(REMOTE_PATH) && \
		docker build \
	    -f Dockerfile \
	    -t $(DOCKER_REGISTRY):$(VERSION) \
	    -t $(DOCKER_REGISTRY):latest \
        --network host \
        --build-arg "HTTP_PROXY=$(ENV_PROXY)" \
        --build-arg "HTTPS_PROXY=$(ENV_PROXY)" \
		--build-arg "ALL_PROXY=$(ENV_PROXY)" \
        --build-arg "NO_PROXY=localhost,192.168.1.200,registry.lazycat.cloud" \
		."

test:
	ssh -t $(REMOTE) "cd $(REMOTE_PATH) && \
		docker run -it --rm \
		--name $(DOCKER_NAME) \
		--network host \
		$(DOCKER_REGISTRY):latest"


inspect:
	ssh -t $(REMOTE) "cd $(REMOTE_PATH) && \
		docker run -it --rm \
		--name $(DOCKER_NAME) \
		--network host \
		$(DOCKER_REGISTRY):latest \
		bash"

push: build
	ssh -t $(REMOTE) "cd $(REMOTE_PATH) && \
		docker push $(DOCKER_REGISTRY):$(VERSION) && \
		docker push $(DOCKER_REGISTRY):latest"

.PHONY: sync-from-gpu sync-to-gpu sync-clean prepare run build test inspect push