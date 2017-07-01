.PHONY: all build clean install vendor

PYMODULE=quickavro
CLEAN=build dist MANIFEST *.egg-info *.egg htmlcov tests/tmp .cache .benchmarks tmp .eggs $(PYMODULE)/*.so
GH_PAGES_SOURCES=docs/source $(PYMODULE) docs/Makefile vendor
CURRENT_BRANCH:=$(shell git rev-parse --abbrev-ref HEAD)
NEW_COMMIT_MESSAGE:=$(shell git log $(CURRENT_BRANCH) -1 --pretty=short --abbrev-commit)

all: build

build:
	@echo "Building quickavro extension ..."
	@python setup.py build --force

install:
	@echo "Installing quickavro ..."
	@pip install --ignore-installed --upgrade .

publish: test build
	python setup.py register
	python setup.py sdist upload

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
	@rm -rf vendor/*.tar.gz avro jansson snappy zlib
	@echo "Done"

initdocs:
	@git branch gh-pages
	@git symbolic-ref HEAD refs/heads/gh-pages
	@rm .git/index
	@git clean -fdx
	@touch .nojekyll
	@git add .nojekyll
	@git commit -m 'Initial commit'
	@git push origin gh-pages

updatedocs:
	@git checkout gh-pages
	@rm -rf docs/build docs/_sources docs/_static *.html *.js
	@git checkout $(CURRENT_BRANCH) $(GH_PAGES_SOURCES)
	@git reset HEAD
	@$(MAKE) -C docs clean html
	@rm -rf _sources _static
	@mv -fv docs/build/html/* .
	@rm -rf $(GH_PAGES_SOURCES) docs/build/html
	@git add -A
	@git commit -m "Generage gh-pages for $(NEW_COMMIT_MESSAGE)"
	@git push origin gh-pages
	@git checkout $(CURRENT_BRANCH)
