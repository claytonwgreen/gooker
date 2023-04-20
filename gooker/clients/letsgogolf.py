import pendulum
from pendulum.date import Date
from pendulum.time import Time
from pendulum.datetime import DateTime

from gooker import base


class LetsGoGolfCourse(base.Course):
    program_id: int


class LetsGoGolfBaseClient(base.TeeTimeClient):
    courses: list[LetsGoGolfCourse]
    base_url = "https://sg-membership20-portalapi-production.azurewebsites.net/api"

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
                "A letsgogolf client may only have one course due to restrictions from their API."
            )

        course = self.courses[0]

        if course not in courses:
            return []

        res = await self.client.get(
            "/courses/reservations_group",
            params={
                "allCartSelected": True,
                "allRatesSelected": True,
                "date": date.isoformat(),
                "min_hour": (earliest_time or self.default_earliest_time).hour,
                "max_hour": (latest_time or self.default_latest_time).hour + 1,
                "max_price": 500,
                "min_price": 0,
                "slug": course.id,
                "programId": course.program_id,
            },
        )
        res.raise_for_status()

        tee_times = []
        for r in res.json()["tee_time_groups"]:
            tee_time: DateTime
            tee_time = pendulum.parser.parse(r["tee_off_at_local"][:-1], tz="America/Los_Angeles")  # type: ignore
            num_players = max(r["players"])
            price = r["max_regular_rate"]
            if (
                tee_time.time() > (earliest_time or self.default_earliest_time)
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


class LosVerdesClient(LetsGoGolfBaseClient):
    courses = [
        LetsGoGolfCourse(
            name="Los Verdes",
            id="los-verdes-golf-course-california",
            is_par_3=False,
            is_9_hole=False,
            is_par_70_plus=True,
            program_id=49,
            booking_url="https://letsgo.golf/los-verdes-golf-course/teeTimes/los-verdes-golf-course-california?date=2023-04-19",
        )
    ]


class MountainMeadowsClient(LetsGoGolfBaseClient):
    courses = [
        LetsGoGolfCourse(
            name="Mountain Meadows",
            id="mountain-meadows-golf-course-california",
            is_par_3=False,
            is_9_hole=False,
            is_par_70_plus=True,
            program_id=48,
            booking_url="https://letsgo.golf/mountain-meadows-golf-course/teeTimes/mountain-meadows-golf-course-california",
        )
    ]


class ElDoradoClient(LetsGoGolfBaseClient):
    courses = [
        LetsGoGolfCourse(
            name="El Dorado",
            id="el-dorado-park-golf-course-california",
            is_par_3=False,
            is_9_hole=False,
            is_par_70_plus=True,
            program_id=56,
            booking_url="https://letsgo.golf/el-dorado-park-golf-course/teeTimes/el-dorado-park-golf-course-california",
        )
    ]


class BrooksideKoinerClient(LetsGoGolfBaseClient):
    courses = [
        LetsGoGolfCourse(
            name="Brookside - Koiner",
            id="brookside-golf-club-c-w-koiner-1-california",
            is_par_3=False,
            is_9_hole=False,
            is_par_70_plus=True,
            program_id=42,
            booking_url=""
        ),
    ]


class BrooksideNayClient(LetsGoGolfBaseClient):
    courses = [
        LetsGoGolfCourse(
            name="Brookside - Nay",
            id="brookside-golf-club-e-o-nay-california",
            is_par_3=False,
            is_9_hole=False,
            is_par_70_plus=True,
            program_id=42,
            booking_url=""
        ),
    ]
