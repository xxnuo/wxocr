ARCH := $(shell uname -m)
UV := ~/.local/bin/uv

prepare:
	$(UV) venv
	$(UV) sync

compile:
	rm -rf wcocr.so
	rm -rf wx
	cp wcocr.cpython-312-$(ARCH)-linux-gnu.so wcocr.so
	cp -r wx_$(ARCH) wx

run:
	$(UV) run main.py

build: compile
	docker build -t wcocr .

test:
	docker run -it --rm wcocr
