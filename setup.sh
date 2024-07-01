#! /usr/bin/bash

PIP="${VENV}/bin/pip3"
PYTHON="${VENV}/bin/python3"
P3_INSTALL="${PIP} -q --disable-pip-version-check install"
prep()
{
    rm -rf "${VENV}"

    "${MIN_PYTHON_VERSION}" -m venv "${VENV}"
    source "${VENV}/bin/activate"

    "${PYTHON}" -V

    ${P3_INSTALL} python-dateutil
    ${P3_INSTALL} requests
    ${P3_INSTALL} glpi-api

    ${P3_INSTALL} cryptography
    ${P3_INSTALL} pyOpenSSL

    "${PIP}" freeze >requirements.txt
}

prep_dev()
{
    ${P3_INSTALL} types-requests
    ${P3_INSTALL} types-python-dateutil
    ${P3_INSTALL} setuptools
    ${P3_INSTALL} types-pyOpenSSL
}

main()
{
    prep

    prep_dev
}

main
