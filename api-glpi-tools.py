from typing import (
    Dict,
    Any,
)

import os
import sys
import json
import logging
import urllib3

import datetime
import dateutil.relativedelta

import glpi_api


log = logging.getLogger()

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning,
)


def make_logger(logger: logging.Logger) -> None:
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


class MyGlpi:
    def __init__(
        self,
        *,
        verify_certs: bool = False,
    ) -> None:
        self.config: Dict[str, Any] = {}
        self.users: Dict[str, Any] = {}
        self.groups: Dict[str, Any] = {}

        self._get_env()
        try:
            self.glpi = glpi_api.GLPI(
                url=self.env["url"],
                apptoken=self.env["apptoken"],
                auth=self.env["usertoken"],
                verify_certs=verify_certs,
            )

        except glpi_api.GLPIError as e:
            log.exception(f"{e}")
            sys.exit(101)

        self.config = self.glpi.get_config()

    @staticmethod
    def _dumps(item: Any) -> None:
        print(
            json.dumps(
                item,
                indent=2,
            ),
            file=sys.stderr,
        )

    def _get_env(
        self,
    ) -> None:
        url = os.getenv("GLPI_URL")
        assert url is not None

        apptoken = os.getenv("GLPI_APPTOKEN")
        assert apptoken is not None

        usertoken = os.getenv("GLPI_USERTOKEN")
        assert usertoken is not None

        self.env = {
            "url": url,
            "apptoken": apptoken,
            "usertoken": usertoken,
        }

    @staticmethod
    def merge_item_field_names(
        item: Any,
        oo: Any,
    ) -> Dict[str, Any]:
        rr: Dict[str, Any] = {}
        for k, v in item.items():
            rr[oo[k]["name"]] = v
        return rr

    def get_user(
        self,
        id: str,
        what: str = "User",
    ) -> Any:
        rr = self.glpi.get_item(
            what,
            item_id=id,
            expand_dropdowns=True,
            range="0-1",
        )
        return rr["name"]

    def get_group(
        self,
        id: str,
        what: str = "Group",
    ) -> Any:
        rr = self.glpi.get_item(
            what,
            item_id=id,
            expand_dropdowns=True,
            range="0-1",
        )
        return rr["name"]

    def get_software(
        self,
        id: str,
        what: str = "Software",
    ) -> Any:
        rr = self.glpi.get_item(
            what,
            item_id=id,
            expand_dropdowns=True,
            range="0-1",
        )
        return rr["name"]

    def get_status(
        self,
        id: str,
        what: str = "State",
    ) -> Any:
        rr = self.glpi.get_item(
            what,
            item_id=id,
            expand_dropdowns=True,
            range="0-1",
        )
        return rr["name"]

    def get_users_active(
        self,
        what: str = "User",
        ignore_left: bool = True,
        only_active: bool = False,
    ) -> None:
        my_range: str = "0-10000"

        u = self.glpi.get_all_items(
            what,
            range=my_range,
        )

        for item in u:
            self._dumps(item)

            if ignore_left is False:
                if item["comment"] and "left" in item["comment"]:
                    continue

            # active

            self.users[item["name"]] = u

    def get_user_email(
        self,
        user_name: str,
        what: str = "UserEmail",
    ) -> str | None:
        my_range: str = "0-10000"

        u = self.glpi.get_all_items(
            what,
            range=my_range,
        )

        for item in u:
            self._dumps(item)

        return None

    def getLicences(
        self,
        future: str,  # only loog at licences that will expire around future date
        what: str = "SoftwareLicense",
    ) -> Any:
        my_range: str = "0-10000"

        u = self.glpi.get_all_items(
            what,
            range=my_range,
            expand_dropdowns=True,
        )

        for item in u:
            exp = item.get("expire")
            if exp and exp <= future:
                self._dumps(item)
                continue

                name = item.get("name")
                admin_group = self.get_group(
                    id=item.get("groups_id_tech"),
                )
                admin_user = self.get_user(
                    id=item.get("users_id_tech"),
                )
                software = self.get_software(
                    id=item.get("softwares_id"),
                )
                state = self.get_status(
                    id=item.get("states_id"),
                )

                print(
                    name,
                    admin_group,
                    admin_user,
                    software,
                    state,
                )

        return None


def main() -> None:
    make_logger(log)

    today = datetime.datetime.now().date()
    future = today - dateutil.relativedelta.relativedelta(days=-30)

    mg = MyGlpi()
    rr = mg.getLicences(
        str(future),
    )
    _ = rr


main()
