from typing import (
    Dict,
    Any,
    List,
    Tuple,
)

import os
import sys
import json
import logging
import urllib3
import ssl

# import math
import datetime
import dateutil.relativedelta
import OpenSSL


from myGlpi import MyGlpi
from myArgs import MyArgs
from myApp import MyApp


from cryptography import x509
from cryptography.hazmat.backends import default_backend


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
    print(common_name.value)

    s1: List[str] = []
    # classes must be subtype of:
    #   https://cryptography.io/en/latest/x509/reference/#cryptography.x509.ExtensionType
    san = loaded_cert.extensions.get_extension_for_class(
        x509.SubjectAlternativeName,
    )
    for s in san:
        s1.append(str(s))

    s2: List[str] = []
    san_dns_names = san.value.get_values_for_type(
        x509.DNSName,
    )
    for s in san_dns_names:
        s2.append(str(s))

    return s1, s2


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


SOCKET_CONNECTION_TIMEOUT_SECONDS = 60
DEFAULT_HTTPS_PORT = 443


def xyz(
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

        common_names_list, san_names_list = extract_names(host, port)
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


def get_cert_info(mg: MyGlpi, future: str | None) -> Any:
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


def email_license_expire_soon(
    app: MyApp,
    future: str,
    mg: MyGlpi,
    url: str,
    admin_email: str,
) -> None:
    app.email_license_expire_soon(
        future=str(future),
        data=mg.getLicences(str(future)),
        url=url,
        admin_email=admin_email,
    )
    return


def certificate_test(
    action: str,
    mg: MyGlpi,
    future: str,
) -> List[Any]:
    if action == "certificate_test_valid":
        rr = get_cert_info(
            mg=mg,
            future=None,
        )
        return rr

    if action == "certificate_test_expire":
        rr = get_cert_info(
            mg=mg,
            future=str(future),
        )
        return rr
    return []


def analyze_certs(
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
                status, cert_info = xyz(a_url)

                pp["cert_url"] = a_url
                pp["cert_info"] = cert_info
                pp["status"] = status

                zz["appliances"].append(pp)

        rr.append(zz)
    return rr


def main() -> None:
    today = datetime.datetime.now().date()
    make_logger(logger=log)
    ma = MyArgs()
    args = ma.get_args()

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    app = MyApp(args=args)

    mg = MyGlpi(
        verify_certs=False,
    )

    days = 30
    future = today - dateutil.relativedelta.relativedelta(
        days=(days * -1),
    )
    app.make_future_list(days_list=args["days"])

    url = mg.get_url()
    admin_email = mg.get_admin_email()

    action = args.get("action")

    if action == "license_expire_test":
        email_license_expire_soon(
            app=app,
            future=str(future),
            mg=mg,
            url=url,
            admin_email=admin_email,
        )
        return

    if action.startswith("certificate_test_"):
        rr = certificate_test(
            action=action,
            mg=mg,
            future=future,
        )
        vv = analyze_certs(
            certs=rr,
            action=action,
        )

        # print(json.dumps(rr, indent=2))
        print(json.dumps(vv, indent=2))
        return rr


main()
