#! /usr/bin/bash

PIP="${VENV}/bin/pip3"
PYTHON="${VENV}/bin/python3"

prep()
{
    rm -rf "${VENV}"

    "${MIN_PYTHON_VERSION}" -m venv "${VENV}"
    source "${VENV}/bin/activate"

    "${PYTHON}" -V

    "${PIP}" -q --disable-pip-version-check install requests python-dateutil
    "${PIP}" -q --disable-pip-version-check install glpi-api

    "${PIP}" freeze >requirements.txt
}

prep_dev()
{
    "${PIP}" -q --disable-pip-version-check install types-requests
    "${PIP}" -q --disable-pip-version-check install types-python-dateutil
    "${PIP}" -q --disable-pip-version-check install setuptools
}

main()
{
    prep

    prep_dev
}

main
