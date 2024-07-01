# makefile , tab=tab, ts=4

VENV 				:= ./venv
ACTIVATE 			:= source ./$(VENV)/bin/activate
MIN_PYTHON_VERSION	:= python3.10
PL_LINTERS			:=	eradicate,mccabe,pycodestyle,pyflakes,pylint
PL_IGNORE			:= E203
LINE_LENGTH 		:= 120
PACKAGE_NAME 		:= *.py
PY_FILES 			:= *.py
TESTING 			:=	1
P3_INSTALL			:=	pip3 -q --disable-pip-version-check install

export MIN_PYTHON_VERSION
export VENV
export TESTING

.PHONY: clean prep black pylama mypy all

all: clean prep run

clean:
	rm -rf $(VENV)
	rm -f *.1 *.2 1 2 *.log

prep: black pylama

black: clean
	./setup.sh ; \
	$(ACTIVATE); \
	$(P3_INSTALL) black; \
	black \
		--line-length $(LINE_LENGTH) \
		$(PY_FILES)

pylama: clean
	./setup.sh ; \
	$(ACTIVATE); \
	$(P3_INSTALL) pylama; \
	pylama \
		--max-line-length $(LINE_LENGTH) \
		--linters "${PL_LINTERS}" \
		--ignore "${PL_IGNORE}" \
		$(PY_FILES)

mypy: clean
	./setup.sh ; \
	$(ACTIVATE); \
	$(P3_INSTALL) mypy; \
	mypy --ignore-missing-imports --strict --no-incremental $(PACKAGE_NAME)

run: run-license run-cert-test

run-license:
	./setup.sh ; \
	$(ACTIVATE); \
	source ~/.glpi_api.env; \
	python3 ./api-glpi-tools.py license_expire_test 2>$@.2 | tee $@.1

run-cert-test:
	./setup.sh ; \
	$(ACTIVATE); \
	source ~/.glpi_api.env; \
	python3 ./api-glpi-tools.py certificate_test_valid 2>$@.2 | tee $@.1


