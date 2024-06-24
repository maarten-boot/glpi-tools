from typing import (
    # Dict,
    # Any,
    List,
)

import os
import sys
import json
import logging
import urllib3
import smtplib

from email.message import EmailMessage

import datetime
import dateutil.relativedelta

from myGlpi import MyGlpi


log = logging.getLogger()

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning,
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
    ch.setLevel(os.getenv("LOG_LEVEL", "WARNING"))

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)


def make_email(
    *,
    from_email_noreply: str,
    to: List[str],
    message: str,
    subject: str,
) -> None:
    mailhost = os.getenv("MAILHOST", None)
    assert mailhost is not None

    msg = EmailMessage()
    msg.set_content(message)
    msg["Subject"] = subject
    msg["From"] = from_email_noreply
    msg["To"] = ", ".join(to)

    print(msg)

    s = smtplib.SMTP("localhost", 25)
    s.send_message(msg)
    s.quit()


def email_licencse_expire_soon(
    *,
    mg: MyGlpi,
    days: int = 30,
) -> None:
    today = datetime.datetime.now().date()
    future = today - dateutil.relativedelta.relativedelta(
        days=(days * -1),
    )

    rr = mg.getLicences(
        str(future),
    )

    url = mg.get_url()

    for item in rr:
        name = item.get("name")
        expire = item.get("expire")
        license_id = item.get("id")

        from_email_noreply = os.getenv("MY_EMAIL_FROM")
        assert from_email_noreply is not None

        my_mail = os.getenv("MY_EMAIL")
        assert my_mail is not None

        to = [str(my_mail)]
        message = f"""
Licence {name} will expire soon: {expire}

{url}/front/softwarelicense.form.php?id={license_id}

{json.dumps(item, indent = 4)}

        """
        subject = f"[glpi] licence '{name}' will expire {expire}"
        make_email(
            from_email_noreply=str(from_email_noreply),
            to=to,
            message=message,
            subject=subject,
        )


def main() -> None:
    make_logger(logger=log)

    mg = MyGlpi()
    email_licencse_expire_soon(mg=mg, days=30)


main()
