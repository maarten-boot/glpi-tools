from typing import (
    Dict,
    Any,
    List,
    Tuple,
)

import os
import logging
import smtplib
import json
import ssl
import datetime
import dateutil.relativedelta
import OpenSSL
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from email.message import EmailMessage
from myGlpi import MyGlpi

SOCKET_CONNECTION_TIMEOUT_SECONDS = 60
DEFAULT_HTTPS_PORT = 443

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

    @staticmethod
    def extract_names(
        host: str,
        port: int,
    ) -> Any:
        certificate: bytes = ssl.get_server_certificate(
            (host, port),
        ).encode(
            "utf-8",
        )
        loaded_cert = x509.load_pem_x509_certificate(
            certificate,
            default_backend(),
        )

        common_name = loaded_cert.subject.get_attributes_for_oid(
            x509.oid.NameOID.COMMON_NAME,
        )

        s1: List[str] = []
        s2: List[str] = []

        for s in common_name:
            s1.append(str(s.value))

        try:
            # classes must be subtype of:
            #   https://cryptography.io/en/latest/x509/reference/#cryptography.x509.ExtensionType
            san = loaded_cert.extensions.get_extension_for_class(
                x509.SubjectAlternativeName,
            )

            san_dns_names = san.value.get_values_for_type(
                x509.DNSName,
            )
            for s in san_dns_names:
                s2.append(str(s))
        except Exception as e:
            if str(e).endswith("<class 'cryptography.x509.extensions.SubjectAlternativeName'> extension was found"):
                pass
            else:
                raise Exception(e)

        return s1, s2

    def xyz(
        self,
        endpoint: str,
    ) -> Tuple[bool, Dict[str, Any]]:
        rr: Dict[str, Any] = {}

        if "https://" not in endpoint.lower():
            rr["expire"] = "Error: No https string could be found"
            return False, rr

        uu = endpoint.lower()[len("https://") :].split("/")[0]
        host, _, specified_port = uu.partition(":")
        if host is None:
            rr["expire"] = "Error: no hostname copuld be extracted"
            return False, rr

        port = int(specified_port or DEFAULT_HTTPS_PORT)

        try:
            cert = ssl.get_server_certificate(
                (
                    host,
                    port,
                ),
            )
            x509 = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM,
                cert,
            )
            rr["subject"] = str(x509.get_subject())
            rr["issuer"] = str(x509.get_issuer())
            rr["serial"] = x509.get_serial_number()

            common_names_list, san_names_list = self.extract_names(
                host,
                port,
            )
            rr["common_names"] = common_names_list
            rr["sam_names_List"] = san_names_list

            zbytes = x509.get_notAfter()
            timestamp = zbytes.decode("utf-8")
        except Exception as e:
            rr["expire"] = f"Error: {e}"
            return False, rr

        expire = (
            datetime.datetime.strptime(
                timestamp,
                "%Y%m%d%H%M%S%z",
            )
            .date()
            .isoformat()
        )
        rr["expire"] = expire
        return True, rr

    @staticmethod
    def get_cert_info(
        mg: MyGlpi,
        future: str | None,
    ) -> Any:
        rr: Dict[str, Any] = {}

        appliances = mg.getAppliances()
        for appliance in appliances:
            appliance_id = appliance.get("id")
            appliance_name = appliance.get("name").strip()

            assocs = mg.getAssociatedItems(
                "Appliance",
                appliance_id,
                "Certificate_Item",
            )
            for assoc in assocs:
                cert_id = assoc.get("certificates_id")
                if cert_id is None:
                    continue

                certificate = mg.get_item(
                    "Certificate",
                    cert_id,
                    expand_dropdowns=True,
                )

                if int(certificate.get("is_deleted")) == 1:
                    continue

                expire = certificate.get("date_expiration")
                if future and expire > future:
                    continue

                certificate_name = certificate.get("name").strip()

                if certificate_name not in rr:
                    rr[certificate_name] = {
                        "cert": certificate,
                        "appliances": [],
                    }

                ss = mg.search(
                    "Appliance",
                    criteria=[
                        {
                            "field": 1,
                            "searchtype": "contains",
                            "value": appliance_name,
                        },
                    ],
                )

                url = None
                if len(ss):
                    url = ss[0].get("PluginWebapplicationsAppliance.address")

                rr[certificate_name]["appliances"].append(
                    {
                        "appliance": appliance,
                        "url": url,
                    },
                )

        return rr

    def analyze_certs(
        self,
        certs: List[Any],
        action: str,
    ) -> None:
        rr: List[Any] = []

        for cert_name, val in certs.items():
            zz: Dict[str, Any] = {}

            zz["cert_name"] = (cert_name,)
            zz["appliances"] = []

            for k, v in val.items():
                if k != "appliances":
                    continue

                for a_data in v:
                    pp: Dict[str, Any] = {}

                    a_url = a_data.get("url")
                    status, cert_info = self.xyz(a_url)

                    pp["cert_url"] = a_url
                    pp["cert_info"] = cert_info
                    pp["status"] = status

                    zz["appliances"].append(pp)

            rr.append(zz)
        return rr

    def certificate_test(
        self,
        action: str,
        mg: MyGlpi,
        future: str,
    ) -> List[Any]:
        if action == "certificate_test_valid":
            rr = self.get_cert_info(
                mg=mg,
                future=None,
            )
            return rr

        if action == "certificate_test_expire":
            rr = self.get_cert_info(
                mg=mg,
                future=str(future),
            )
            return rr
        return []
