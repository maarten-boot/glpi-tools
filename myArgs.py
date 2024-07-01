from typing import (
    Dict,
    Any,
)

import os
import sys
import logging
import argparse
import datetime

log = logging.getLogger(__name__)


class MyArgs:
    def __init__(
        self,
    ) -> None:
        self.args: Dict[str, Any] = self._do_args()
        self.args["today"] = datetime.datetime.now().date()
        self.args["prog"] = os.path.basename(sys.argv[0])

    @staticmethod
    def _do_args() -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        prog = os.path.basename(
            sys.argv[0],
        )
        usage = ""
        epilog = ""
        description = ""

        parser = argparse.ArgumentParser(
            description=description,
            usage=usage,
            epilog=epilog,
            prog=prog,
        )

        parser.add_argument(
            "--no-verify-cert",
            action="store_true",
            help="do not verify the https cert",
        )
        parser.add_argument(
            "--glpi-server",
            "-S",
            help="the glpi server url",
        )
        parser.add_argument(
            "--glpi-apptoken",
            "-T",
            help="the glpi app token",
        )
        parser.add_argument(
            "--glpi-usertoken",
            "-U",
            help="the glpi user token",
        )
        parser.add_argument(
            "--testing",
            "-t",
            action="store_true",
            help="do not send any mails during testing",
        )
        parser.add_argument(
            "action",
            help="what action do you want to execute",
        )
        days = sorted(
            [
                90,
                60,
                28,
                21,
                14,
                7,
                6,
                5,
                4,
                3,
                2,
                1,
            ],
            reverse=True,
        )
        days_s = ", ".join(f"{n}" for n in days)
        parser.add_argument(
            "--days",
            "-d",
            action="append",
            nargs="*",
            default=days,
            help=f"At what days do you want emails to be send; default: {days_s}",
        )

        actions = [
            "certificate_expire_check",
            "licence_expire_check",
        ]

        _ = actions

        for k, v in vars(parser.parse_args()).items():
            result[k] = v

        return result

    def get_args(self) -> Dict[str, Any]:
        return self.args
