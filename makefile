# makefile , tab=tab, ts=4

VENV 				:= ./venv
ACTIVATE 			:= source ./$(VENV)/bin/activate
MIN_PYTHON_VERSION	:= python3.12
PL_LINTERS			:=	eradicate,mccabe,pycodestyle,pyflakes,pylint
LINE_LENGTH 		:= 120
PACKAGE_NAME 		:= *.py
PY_FILES 			:= *.py

export MIN_PYTHON_VERSION
export VENV

.PHONY: clean prep black pylama mypy all

all: clean prep run

clean:
	rm -rf $(VENV)
	rm -f *.1 *.2 1 2 *.log

prep: black pylama mypy

black: clean
	./setup.sh ; \
	$(ACTIVATE); \
	pip3 -q --disable-pip-version-check install black; \
	black \
		--line-length $(LINE_LENGTH) \
		$(PY_FILES)

pylama: clean
	./setup.sh ; \
	$(ACTIVATE); \
	pip3 -q --disable-pip-version-check install pylama; \
	pylama \
		--max-line-length $(LINE_LENGTH) \
		--linters "${PL_LINTERS}" \
		--ignore "${PL_IGNORE}" \
		$(PY_FILES)

mypy: clean
	./setup.sh ; \
	$(ACTIVATE); \
	pip3 -q --disable-pip-version-check install mypy; \
	pip3 -q --disable-pip-version-check install types-requests; \
	mypy --ignore-missing-imports --strict --no-incremental $(PACKAGE_NAME)

run:
	./setup.sh ; \
	$(ACTIVATE); \
	source ~/.glpi_api.env; \
	python3 ./api-glpi-tools.py  2>2 | tee 1
