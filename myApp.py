from typing import (
    Dict,
    Any,
    List,
)

import os
import logging
import smtplib

import json

import datetime
import dateutil.relativedelta

from email.message import EmailMessage

log = logging.getLogger(__name__)


def json_serial(
    obj: Any,
) -> str:
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(
        obj,
        (
            datetime.datetime,
            datetime.date,
        ),
    ):
        return obj.isoformat()

    raise TypeError("Type %s not serializable" % type(obj))


def my_jdump(
    obj: Any,
    indent: int = 2,
    sort_keys: bool = True,
) -> str:
    return json.dumps(
        obj,
        indent=indent,
        default=json_serial,
        sort_keys=sort_keys,
    )


class MyApp:
    def __init__(
        self,
        *,
        args: Dict[str, Any] = {},
    ) -> None:
        self.args = args

        self.args["mailhost"] = os.getenv("MAILHOST", None)
        assert self.args.get("mailhost") is not None

        self.args["mailhost_port"] = os.getenv("MAILHOST_PORT", None)
        assert self.args.get("mailhost_port") is not None

    def _make_email(
        self,
        *,
        from_email_noreply: str,
        to: List[str],
        message: str,
        subject: str,
        testing: bool = False,
    ) -> None:

        msg = EmailMessage()
        msg.set_content(message)

        msg["Subject"] = subject
        msg["From"] = from_email_noreply
        msg["To"] = ", ".join(to)

        if testing:
            print("TESTING")
            print(msg)
            return

        s = smtplib.SMTP(
            str(self.args.get("mailhost")),
            int(str(self.args.get("mailhost_port"))),
        )
        s.send_message(msg)
        s.quit()

    def _extract_mails(
        self,
        *,
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

    def make_future_list(
        self,
        *,
        days_list: List[int],
    ) -> Dict[str, Any]:
        today = datetime.datetime.now().date()
        days_list = sorted(days_list)

        rr: Dict[str, Any] = {
            "days": days_list,
            "future": {},
            "oldest": max(days_list),
            "today": str(today),
        }

        for days in days_list:
            if days <= 0:
                continue

            future = today - dateutil.relativedelta.relativedelta(
                days=(days * -1),
            )
            rr["future"][days] = future

        return rr

    def email_license_expire_soon(
        self,
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

            mails = self._extract_mails(item=item)
            if len(mails) == 0:
                mails.append(admin_email)

            message = f"""
Licence {name} will expire soon: {expire}

{url}/front/softwarelicense.form.php?id={license_id}

{my_jdump(item)}

"""

            subject = f"[glpi] licence '{name}' will expire {expire}"

            z = os.getenv("TESTING")
            testing = True
            if z is None or str(z) == "" or int(z) == 0:
                testing = False

            self._make_email(
                from_email_noreply=str(from_email_noreply),
                to=mails,
                message=message,
                subject=subject,
                testing=testing,
            )
