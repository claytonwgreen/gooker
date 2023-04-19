import logging
import asyncio
import uuid
import time
import random

from pendulum.date import Date

from gooker import base
from gooker import search
from gooker.args import parse_args
from gooker.database import DBClient


MIN_SLEEP = 60 * 7
MAX_SLEEP = 60 * 15

logger = logging.getLogger(__name__)


def main():
    args = parse_args()
    if args.command == "find-tee-times":
        if isinstance(args.start, Date):
            start_date = args.start
            start_time = None
        else:
            start_date = args.start.date
            start_time = args.start.time

        if isinstance(args.end, Date):
            end_date = args.end
            end_time = None
        else:
            end_date = args.end.date
            end_time = args.end.time

        tee_time_search = base.TeeTimeSearchParams(
            start_date=start_date,
            start_time=start_time,
            end_date=end_date,
            end_time=end_time,
            courses=args.courses,
            par_70_plus=args.par_70_plus,
            eighteen_holes=args.eighteen_holes,
            nine_holes=args.nine_holes,
            min_players=args.min_players,
            earliest_time=args.earliest_time,
            latest_time=args.latest_time,
            max_price=args.max_price,
        )

        if args.create_search:
            search_id = uuid.uuid4()
            with DBClient() as client:
                client.insert_tee_time_search(
                    base.TeeTimeSearch(
                        id=search_id,
                        notification_method=args.notification_method,
                        notification_destination=args.notification_destination,
                        search_params=tee_time_search,
                    )
                )
        else:
            tee_time_list = asyncio.run(search.find_tee_times(tee_time_search))
            tee_times = base.TeeTimes()
            for t in tee_time_list:
                tee_times.add_tee_time(t)
            print(tee_times.create_tee_time_message())
    elif args.command == "poll-for-tee-times":
        while True:
            sleep_time = random.randint(MIN_SLEEP, MAX_SLEEP)
            logger.info(
                f"sleeping for {sleep_time//60} minutes {sleep_time%60} seconds"
            )
            time.sleep(sleep_time)
            with DBClient() as client:
                asyncio.run(search.check_for_times(client))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
