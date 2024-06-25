from typing import (
    Dict,
    Any,
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
    testing: bool = False,
) -> None:
    print(testing)
    exit(0)

    mailhost = os.getenv("MAILHOST", None)
    assert mailhost is not None

    mailhost_port = os.getenv("MAILHOST_PORT", None)
    assert mailhost_port is not None

    msg = EmailMessage()
    msg.set_content(message)
    msg["Subject"] = subject
    msg["From"] = from_email_noreply
    msg["To"] = ", ".join(to)

    if testing:
        print(msg)
        return

    s = smtplib.SMTP(
        mailhost,
        int(mailhost_port),
    )
    s.send_message(msg)
    s.quit()


def extract_mails(
    item: Dict[str, Any],
) -> List[str]:
    mails = []

    k = "tech_user_email"
    mail = item.get(k)
    if mail:
        mails.append(mail)

    k = "tech_group_emails"
    mail = item.get(k)
    if mail:
        for k, v in mail.items():
            mails.append(v)

    return mails


def email_licencse_expire_soon(
    *,
    future: str,
    data: List[Dict[str, Any]],
    url: str,
    admin_email: str,
) -> None:
    for item in data:
        name = item.get("name")
        expire = item.get("expire")
        license_id = item.get("id")

        from_email_noreply = os.getenv("MY_EMAIL_FROM")
        assert from_email_noreply is not None

        mails = extract_mails(item=item)
        if len(mails) == 0:
            mails.append(admin_email)

        message = f"""
Licence {name} will expire soon: {expire}

{url}/front/softwarelicense.form.php?id={license_id}

{json.dumps(item, indent=4)}

        """

        subject = f"[glpi] licence '{name}' will expire {expire}"

        z = os.getenv("TESTING")
        testing = True
        if z is None or str(z) == "" or int(z) == 0:
            testing = False

        make_email(
            from_email_noreply=str(from_email_noreply),
            to=mails,
            message=message,
            subject=subject,
            testing=testing,
        )


def main() -> None:
    make_logger(logger=log)
    days = 30

    mg = MyGlpi(
        verify_certs=False,
        debug=False,
    )

    today = datetime.datetime.now().date()
    future = today - dateutil.relativedelta.relativedelta(
        days=(days * -1),
    )

    url = mg.get_url()
    admin_email = mg.get_admin_email()

    rr = mg.getLicences(
        str(future),
    )

    email_licencse_expire_soon(
        future=str(future),
        data=rr,
        url=url,
        admin_email=admin_email,
    )


main()
