.PHONY: all build clean install vendor

PYMODULE=quickavro

all: build

build:
	@echo "Building quickavro extension ..."
	@python setup.py build --force

install:
	@echo "Installing quickavro ..."
	@python setup.py install --user

build-wheel:
	@python setup.py bdist_wheel

install-wheel: build-wheel
	@pip install --force-reinstall --upgrade dist/*.whl --user

clean:
	@echo "Cleaning up existing build files..."
	@rm -rf build dist MANIFEST *.egg-info htmlcov tests/tmp .cache .benchmarks tmp
	@find . -name '__pycache__' -delete -print -o -name '*.pyc' -delete -print

clean-all: clean
	$(MAKE) -C vendor clean

vendor:
	@echo -n "Downloading vendor files ..."
	@$(MAKE) -C vendor download >/dev/null 2>&1
	@echo "Done"

test:
	@py.test tests/
	@rm -rf tests/tmp
	@find . -name '__pycache__' -delete -o -name '*.pyc' -delete
