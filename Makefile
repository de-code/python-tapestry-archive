VENV = venv
PIP = $(VENV)/bin/pip
PYTHON = $(VENV)/bin/python

ARGS =
PYTEST_WATCH_MODULES = tests

venv-clean:
	@if [ -d "$(VENV)" ]; then \
		rm -rf "$(VENV)"; \
	fi


venv-create:
	python3 -m venv $(VENV)


venv-activate:
	chmod +x venv/bin/activate
	bash -c "venv/bin/activate"


dev-install:
	$(PIP) install --disable-pip-version-check \
		-r requirements.build.txt \
		-r requirements.dev.txt \
		-r requirements.txt


dev-venv: venv-create dev-install


dev-flake8:
	$(PYTHON) -m flake8 tapestry_archive tests

dev-pylint:
	$(PYTHON) -m pylint tapestry_archive tests

dev-mypy:
	$(PYTHON) -m mypy tapestry_archive tests


dev-lint: dev-flake8 dev-pylint dev-mypy

dev-unittest:
	$(PYTHON) -m pytest -p no:cacheprovider $(ARGS) tests

dev-watch:
	$(PYTHON) -m pytest_watch -- -p no:cacheprovider $(ARGS) $(PYTEST_WATCH_MODULES)

dev-test: dev-lint dev-unittest


run:
	$(PYTHON) -m tapestry_archive.cli
