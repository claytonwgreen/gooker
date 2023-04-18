from typing import Union
import asyncio
import argparse
import logging
import re
import os
import uuid

import pendulum
from pendulum.date import Date
from pendulum.datetime import DateTime
from pendulum.time import Time

from gooker.clients import clients


TIME_FMT = "HH:mm:ss"
DATE_FMT = "YYYY-MM-DD"
DATETIME_FMT = "YYY-MM-DDTHH:mm:ss"

logger = logging.getLogger(__name__)
email_regex = re.compile(
    r"""(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"""
)


def _parse_date_or_dt(val: str) -> Union[Date, DateTime]:
    try:
        return pendulum.from_format(val, DATE_FMT).date()
    except ValueError:
        pass

    try:
        return pendulum.from_format(val, DATETIME_FMT)
    except ValueError:
        pass

    raise ValueError(f"'{val}' does not match form {DATE_FMT} or {DATETIME_FMT}")


def _parse_time(val: str) -> Time:
    try:
        return pendulum.from_format(val, TIME_FMT).time()
    except ValueError:
        pass

    raise ValueError(f"'{val}' does not match form {TIME_FMT}")


def _validate_args(args):
    if args.start > args.end:
        raise ValueError("`start` must be before `end`")

    if (
        args.earliest_time
        and args.latest_time
        and args.earliest_time > args.latest_time
    ):
        raise ValueError("`earliest_time` must be before `latest_time`")

    if args.nine_holes and args.eighteen_holes:
        raise ValueError(
            "`nine-holes` and `eighteen-holes` cannot both be specified, use neither if you want both returned"
        )

    if args.max_price is not None and args.max_price < 0:
        raise ValueError("max_price cannot be negative")

    if args.create_search:
        if args.notification_method == "email":
            for address in args.notification_destination:
                if not re.match(email_regex, address):
                    raise ValueError(f"{address} is not a valid email address")


def parse_args():
    now = pendulum.now()
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "command",
        choices=["find-tee-times", "poll-for-tee-times"],
        help="task to perform",
    )
    arg_parser.add_argument(
        "--start",
        type=_parse_date_or_dt,
        help=f"start date or datetime. Format-> {DATE_FMT} or {DATETIME_FMT}. Defaults to the next Saturday or today if it is Saturday or Sunday before 5pm",
        default=now.date()
        if now.day_of_week == 6
        or (now.day_of_week == 0 and now.time() < Time(17, 0, 0))
        else now.date().add(days=6 - now.day_of_week),
    )
    arg_parser.add_argument(
        "--end",
        type=_parse_date_or_dt,
        help=f"end date or datetime. Format-> {DATE_FMT} or {DATETIME_FMT}. Defaults to the next Sunday or today if it is Sunday before 5pm.",
        default=now.date()
        if now.day_of_week == 0 and now.time() < Time(17, 0, 0)
        else now.date().add(days=7 - now.day_of_week),
    )
    arg_parser.add_argument(
        "--courses",
        type=str,
        choices=[course.name for client in clients for course in client.courses],
        help="courses to search",
        nargs="*",
    )
    arg_parser.add_argument(
        "--min-players",
        type=int,
        help="minimum number of players",
        default=4,
    )
    arg_parser.add_argument(
        "--earliest-time",
        type=_parse_time,
        help=f"only tee times after a certain time. Format-> {TIME_FMT}",
    )
    arg_parser.add_argument(
        "--latest-time",
        type=_parse_time,
        help=f"only tee times before a certain time. Format-> {TIME_FMT}",
    )
    arg_parser.add_argument(
        "--par-70-plus",
        action="store_true",
        help="only courses with par 70+",
    )
    arg_parser.add_argument(
        "--eighteen-holes",
        action="store_true",
        help="only 18 hole courses",
    )
    arg_parser.add_argument(
        "--nine-holes",
        action="store_true",
        help="only 9 hole courses",
    )
    arg_parser.add_argument(
        "--max-price",
        type=int,
        help="max price per player",
        default=None,
    )
    arg_parser.add_argument(
        "--notification-method",
        type=str,
        choices=["email"],
        help="how to get notified about new tee times",
        default="email",
    )
    arg_parser.add_argument(
        "--notification-destination",
        type=str,
        help="where to send notifications",
        nargs="*",
        default=[os.environ.get("DEFAULT_EMAIL_DESTINATION") or "barack@obama.com"],
    )
    arg_parser.add_argument(
        "--create-search",
        action="store_true",
        help="If true, get notified when tee times matching parameters become available",
    )

    args = arg_parser.parse_args()
    _validate_args(args)
    return args
