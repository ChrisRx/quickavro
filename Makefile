.PHONY: all build clean install vendor

PYMODULE=quickavro
CLEAN=build dist MANIFEST *.egg-info *.egg htmlcov tests/tmp .cache .benchmarks tmp .eggs

all: build

build:
	@echo "Building quickavro extension ..."
	@python setup.py bdist_wheel

install:
	@echo "Installing quickavro ..."
	@pip install --ignore-installed --upgrade .

publish: test build
	python setup.py register
	python setup.py bdist_wheel upload

test:
	@py.test tests/
	@rm -rf tests/tmp
	@find . -name '__pycache__' -delete -o -name '*.pyc' -delete

vendor:
	@echo -n "Downloading vendor files ..."
	@$(MAKE) -C vendor download >/dev/null 2>&1
	@echo "Done"

clean:
	@echo "Cleaning up existing build files..."
	@rm -rf $(CLEAN)
	@find . -name '__pycache__' -delete -print -o -name '*.pyc' -delete -print

clean-vendor:
	@echo -n "Cleaning up vendor files..."
	@rm -rf vendor/*
	@echo "Done"
