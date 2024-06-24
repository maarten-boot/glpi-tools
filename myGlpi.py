from typing import (
    Dict,
    Any,
    # List,
)

import os
import sys
import json
import logging
import urllib3

import glpi_api


log = logging.getLogger()

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning,
)


class MyGlpi:
    def __init__(
        self,
        *,
        verify_certs: bool = False,
    ) -> None:
        self.config: Dict[str, Any] = {}
        self.users: Dict[str, Any] = {}
        self.groups: Dict[str, Any] = {}
        self.emails: Dict[str, str] = {}

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
        self.get_emails()

    def get_url(self) -> str:
        return self.env["url"]

    def get_emails(
        self,
        what: str = "UserEmail",
    ) -> None:
        my_range: str = "0-10000"

        u = self.glpi.get_all_items(
            what,
            range=my_range,
            expand_dropdowns=True,
        )

        for item in u:
            self._dumps(item)
            email = item.get("email")
            login = item.get("users_id")
            is_default = bool(item.get("is_default"))
            if is_default:
                self.emails[login] = email

    @staticmethod
    def _dumps(item: Any) -> None:
        return

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

    def get_user_email(
        self,
        user_name: str,
    ) -> str | None:
        if user_name is None:
            return None

        # read from cache
        return self.emails.get(user_name)

    def get_group_by_name(self, group: str) -> int | None:
        # return the group id
        rr = self.glpi.get_all_items(
            "Group",
            range="0-10000",
            searchText={
                "name": group,
            },
            expand_dropdowns=True,
            only_id=True,
        )

        if len(rr) == 0:
            return None
        return int(rr[0]["id"])

    def expand_group_to_emails(
        self,
        group: str,
    ) -> Dict[str, str | None]:
        # https://*ip*/glpi/apirest.php/group/*groupid*/Group_User

        rr: Dict[str, str | None] = {}
        group_id = self.get_group_by_name(group)

        print(group_id)

        z = self.glpi.get_sub_items(
            itemtype="Group",
            item_id=group_id,
            sub_itemtype="Group_User",
            expand_dropdowns=True,
        )
        for item in z:
            user_name = item.get("users_id")
            if user_name:
                rr[user_name] = self.emails.get(user_name)
        return rr

    def getLicences(
        self,
        future: str,  # only loogkat licences that will expire before future date
        what: str = "SoftwareLicense",
    ) -> Any:
        def orNone(item: Any) -> Any:
            if item == 0:
                return None
            if item == "":
                return None

            return item

        my_range: str = "0-10000"

        u = self.glpi.get_all_items(
            what,
            range=my_range,
            expand_dropdowns=True,
        )

        result = []
        for item in u:
            exp = item.get("expire")
            if exp is None or exp > future:
                continue

            if item.get("is_deleted"):
                continue

            self._dumps(item)

            user = orNone(item.get("users_id_tech"))
            email = self.get_user_email(user)

            group = orNone(item.get("groups_id_tech"))
            if self.groups.get(group) is None:
                self.groups[group] = self.expand_group_to_emails(group)

            emails = self.groups[group]

            z = {
                "id": item.get("id"),
                "name": orNone(item.get("name")),
                "tech_user": user,
                "tech_user_email": email,
                "software": orNone(item.get("softwares_id")),
                "state": orNone(item.get("states_id")),
                "expire": orNone(item.get("expire")),
                "comment": orNone(item.get("comment")),
                "tech_group": group,
                "tech_group_emails": emails,
            }
            result.append(z)

        return result
