import pendulum
from pendulum.date import Date
from pendulum.time import Time

from gooker import base


class ForeUpBaseClient(base.TeeTimeClient):
    courses: list[base.Course]
    base_url = "https://foreupsoftware.com/index.php/api"

    async def get_tee_times(
        self,
        courses: list[base.Course],
        date: Date,
        earliest_time: Time | None = None,
        latest_time: Time | None = None,
        min_players: int = 4,
        max_price: int | None = None,
    ) -> list[base.TeeTime]:
        if len(self.courses) > 1:
            raise ValueError(
                "A foreup client may only have one course due to restrictions from their API."
            )

        course = self.courses[0]

        if course not in courses:
            return []

        res = await self.client.get(
            "/booking/times",
            params={
                "time": "all",
                "date": date.format("MM-DD-YYYY"),
                "holes": "all",
                "players": 0,
                "api_key": "no_limits",
                "schedule_id": course.id,
            },
        )
        res.raise_for_status()

        tee_times = []
        for r in res.json():
            tee_time = pendulum.from_format(r["time"], "YYYY-MM-DD HH:mm", tz="America/Los_Angeles")  # type: ignore
            num_players = r["available_spots"]
            price = r["green_fee"]
            if (
                tee_time.time() > (earliest_time or self.default_earliest_time)
                and tee_time.time() < (latest_time or self.default_latest_time)
                and num_players >= min_players
                and (max_price is None or r["green_fee"] <= max_price)
            ):
                tee_times.append(
                    base.TeeTime(
                        course=course,
                        tee_time=tee_time,
                        num_golfers=num_players,
                        price=price,
                    )
                )

        return tee_times


class WestchesterClient(ForeUpBaseClient):
    courses = [
        base.Course(
            name="Westchester",
            id=3786,
            is_par_3=False,
            is_9_hole=False,
            is_par_70_plus=False,
            booking_url="https://foreupsoftware.com/index.php/booking/20137/3786#/teetimes",
        ),
    ]


class RusticCanyonClient(ForeUpBaseClient):
    courses = [
        base.Course(
            name="Rustic Canyon",
            id=9285,
            is_par_3=False,
            is_9_hole=False,
            is_par_70_plus=True,
            booking_url="https://foreupsoftware.com/index.php/booking/21903/9285#teetimes",
        ),
    ]

