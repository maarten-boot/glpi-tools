from typing import (
    Any,
)

import os
import sys
import json
import logging
import urllib3

import datetime
import dateutil.relativedelta


from myGlpi import MyGlpi
from myArgs import MyArgs
from myApp import MyApp


log = logging.getLogger()

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning,
)


def json_serial(obj: Any) -> str:
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


def my_jdump(obj: Any, indent: int = 2, sort_keys: bool = True) -> str:
    return json.dumps(
        obj,
        indent=indent,
        default=json_serial,
        sort_keys=sort_keys,
    )


def make_logger(*, logger: logging.Logger) -> None:
    logger.setLevel(logging.DEBUG)

    progName = os.path.basename(sys.argv[0])
    if progName.endswith(".py"):
        progName = progName[:-3]
    fileName = f"{progName}.log"

    fh = logging.FileHandler(fileName)
    fh.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(
        os.getenv(
            "LOG_LEVEL",
            "WARNING",
        ),
    )

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)


def main() -> None:
    today = datetime.datetime.now().date()

    # ctx = ssl.create_default_context()
    # ctx.check_hostname = False
    # ctx.verify_mode = ssl.CERT_NONE

    ma = MyArgs()
    ma.make_logger(logger=log)
    args = ma.get_args()
    app = MyApp(args=args)
    mg = MyGlpi(
        verify_certs=False,
    )

    days = 30
    future = today - dateutil.relativedelta.relativedelta(
        days=(days * -1),
    )
    app.make_future_list(
        days_list=args["days"],
    )

    url = mg.get_url()
    admin_email = mg.get_admin_email()
    action = args.get("action")

    if action == "license_expire_test":
        app.email_license_expire_soon(
            future=str(future),
            data=mg.getLicences(str(future)),
            url=url,
            admin_email=admin_email,
        )
        return

    if action.startswith("certificate_test_"):
        rr = app.certificate_test(
            action=action,
            mg=mg,
            future=future,
        )
        vv = app.analyze_certs(
            certs=rr,
            action=action,
        )

        print(json.dumps(vv, indent=2))
        return rr


main()
