import pendulum
from pendulum.date import Date
from pendulum.time import Time
from pendulum.datetime import DateTime

from gooker import base


class TeeItUpCourse(base.Course):
    slug: str


class TeeItUpBaseClient(base.TeeTimeClient):
    courses: list[TeeItUpCourse]
    base_url = "https://phx-api-be-east-1b.kenna.io/v2"

    async def get_tee_times(
        self,
        courses: list[TeeItUpCourse],
        date: Date,
        earliest_time: Time | None = None,
        latest_time: Time | None = None,
        min_players: int = 4,
        max_price: int | None = None,
    ) -> list[base.TeeTime]:
        if len(self.courses) > 1:
            raise ValueError(
                "A teeitup client may only have one course due to restrictions from their API."
            )

        course = self.courses[0]

        if course not in courses:
            return []

        res = await self.client.get(
            "/tee-times",
            params={"date": date.isoformat(), "facilityIds": course.id},
            headers={"x-be-alias": course.slug},
        )
        res.raise_for_status()

        tee_times = []
        for r in res.json()[0]["teetimes"]:
            tee_time: DateTime
            tee_time = pendulum.parser.parse(r["teetime"]).in_timezone("America/Los_Angeles")  # type: ignore
            rate = r["rates"][0]
            num_players = max(rate["allowedPlayers"])
            price = int(rate["greenFeeCart"]) / 100
            holes = rate["holes"]
            if (
                holes == 18
                and tee_time.time() > (earliest_time or self.default_earliest_time)
                and tee_time.time() < (latest_time or self.default_latest_time)
                and num_players >= min_players
                and (max_price is None or price <= max_price)
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


class IndustryHillsIkeClient(TeeItUpBaseClient):
    courses = [
        TeeItUpCourse(
            name="Industry Hills - Ike",
            id=6430,
            is_par_3=False,
            is_9_hole=False,
            is_par_70_plus=True,
            booking_info="(626) 810-4653",
            slug="industry-hills-golf-club-ike-course",
        )
    ]


class IndustryHillsBabeClient(TeeItUpBaseClient):
    courses = [
        TeeItUpCourse(
            name="Industry Hills - Babe",
            id=4735,
            is_par_3=False,
            is_9_hole=False,
            is_par_70_plus=True,
            booking_info="(626) 810-4653",
            slug="industry-hills-golf-club-babe-course",
        )
    ]
