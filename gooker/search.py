import logging
import asyncio
import datetime

import pendulum
from pendulum.date import Date
from pendulum.time import Time

from gooker import notify
from gooker import base
from gooker.clients import clients
from gooker.database import DBClient


logger = logging.getLogger(__name__)


def _build_itervals(
    start_date: Date,
    start_time: Time | None,
    end_date: Date,
    end_time: Time | None,
    earliest_time: Time | None,
    latest_time: Time | None,
) -> list[tuple[Date, Time | None, Time | None]]:
    cur_date = start_date
    cur_earliest_time = start_time
    cur_latest_time = None

    intervals = []
    while cur_date <= end_date:
        if cur_date == end_date:
            cur_latest_time = end_time

        intervals.append(
            (
                cur_date,
                cur_earliest_time or earliest_time,
                cur_latest_time or latest_time,
            )
        )
        cur_date = cur_date + datetime.timedelta(days=1)

    return intervals


def _filter_courses(
    base_courses: list[base.Course],
    par_70_plus: bool,
    eighteen_holes: bool,
    nine_holes: bool,
) -> list[base.Course]:
    courses = []
    for course in base_courses:
        if par_70_plus and not course.is_par_70_plus:
            continue
        if eighteen_holes and course.is_9_hole:
            continue
        if nine_holes and not course.is_9_hole:
            continue
        courses.append(course)

    return courses


async def find_tee_times(search: base.TeeTimeSearchParams) -> list[base.TeeTime]:
    tee_times = base.TeeTimes()
    intervals = _build_itervals(
        search.start_date,
        search.start_time,
        search.end_date,
        search.end_time,
        search.earliest_time,
        search.latest_time,
    )
    courses = _filter_courses(
        [
            course
            for client in clients
            for course in client.courses
            if search.courses is None or course.name in search.courses
        ],
        search.par_70_plus,
        search.eighteen_holes,
        search.nine_holes,
    )

    async def _get_client_tee_times(
        client: type[base.TeeTimeClient],
        intervals: list[tuple[Date, Time | None, Time | None]],
        courses: list[base.Course],
        min_players: int = 4,
        earliest_time: Time | None = None,
        latest_time: Time | None = None,
        max_price: int | None = None,
    ) -> list[base.TeeTime]:
        client_tee_times: list[base.TeeTime] = []
        async with client() as c:
            for date, earliest_time, latest_time in intervals:
                try:
                    client_tee_times.extend(
                        await c.get_tee_times(
                            courses=courses,
                            date=date,
                            earliest_time=earliest_time,
                            latest_time=latest_time,
                            min_players=min_players,
                            max_price=max_price,
                        )
                    )
                except Exception as e:
                    logger.warning(f"Exception encountered while running {client.__name__} for {date}: {e.__class__.__name__}")  # type: ignore

        return client_tee_times

    tee_times = []
    for tee_time_list in await asyncio.gather(
        *[
            _get_client_tee_times(
                client,
                intervals,
                courses,
                search.min_players,
                search.earliest_time,
                search.latest_time,
                search.max_price,
            )
            for client in clients
        ]
    ):
        tee_times.extend(tee_time_list)

    return tee_times


async def check_for_times(client: DBClient):
    cur_searches = client.get_current_tee_time_searches()
    logger.info(f"Found {len(cur_searches)} current searches")
    for search in cur_searches:
        if search.search_params.end_date < pendulum.now().date():
            logger.info(
                f"Deleting search {search.id} as {search.search_params.end_date} has passed"
            )
            client.delete_tee_time_search(search)
            continue

        logger.info(f"Checking for new tee times for {search.id}")
        cur_results = client.get_current_tee_time_search_results(search.id)
        client_results = await find_tee_times(search.search_params)
        new_results = [t for t in client_results if t not in cur_results]
        missing_results = [t for t in cur_results if t not in client_results]

        if new_results:
            logger.info(f"Found {len(new_results)} new tee times for {search.id}")
            tee_times = base.TeeTimes()
            for t in new_results:
                tee_times.add_tee_time(t)
            logger.info(
                f"Sending {search.notification_method} for {search.id} to {search.notification_destination}"
            )
            await notify.send_message(
                search.notification_method,
                f"Tee Times found for {search.id}",
                f"{tee_times.create_tee_time_message()}\n\n{search.search_params.create_search_param_message()}",
                search.notification_destination,
            )
            client.insert_tee_time_search_results(search.id, new_results)
        else:
            logger.info(f"Found no new tee times for {search.id}")

        if missing_results:
            logger.info(f"Deleting {len(missing_results)} tee_times for {search.id}")
            client.delete_tee_time_search_results(search.id, missing_results)
