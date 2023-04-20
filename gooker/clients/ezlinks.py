import pendulum
from pendulum.date import Date
from pendulum.time import Time

from gooker import base


class EZLinksBaseClient(base.TeeTimeClient):
    base_url: str
    courses: list[base.Course]

    async def get_tee_times(
        self,
        courses: list[base.Course],
        date: Date,
        earliest_time: Time | None = None,
        latest_time: Time | None = None,
        min_players: int = 4,
        max_price: int | None = None,
    ) -> list[base.TeeTime]:
        matching_courses = [course for course in courses if course in self.courses]

        if not matching_courses:
            return []

        res = await self.client.post(
            "/search/search",
            json={
                "p01": [c.id for c in matching_courses],
                "p02": date.format("MM/DD/YYYY"),
                "p03": (earliest_time or self.default_earliest_time).format("h:mm A"),
                "p04": (latest_time or self.default_latest_time).format("h:mm A"),
                "p05": 0,
                "p06": min_players,
                "p07": False,
            },
        )
        res.raise_for_status()

        tee_times = []
        for r in res.json()["r06"]:
            num_players = r["r11"]
            price = float(r["r25"])
            if num_players < min_players or (
                max_price is not None and price > max_price
            ):
                continue

            tee_time = base.TeeTime(
                course=next(c for c in matching_courses if c.id == r["r07"]),
                tee_time=pendulum.parser.parse(r["r15"], tz="America/Los_Angeles"),  # type: ignore
                num_golfers=num_players,
                price=price,
            )

            # search for existing tee time, meaning this is a different price
            # for same tee time. Keep the one with higher price
            try:
                existing_tee_time_idx = tee_times.index(tee_time)
                if tee_time.price > tee_times[existing_tee_time_idx].price:
                    tee_times[existing_tee_time_idx] = tee_time
            except ValueError:
                tee_times.append(tee_time)

        return tee_times


class LosRoblesClient(EZLinksBaseClient):
    base_url = "https://losrobles.ezlinksgolf.com/api"
    courses = [
        base.Course(
            name="Los Robles",
            id=6070,
            is_par_3=False,
            is_9_hole=False,
            is_par_70_plus=True,
            booking_url="https://losrobles.ezlinksgolf.com/index.html#/search",
        )
    ]


class TeirraRejadaClient(EZLinksBaseClient):
    base_url = "https://tierrarejadapubpp.ezlinksgolf.com/api"
    courses = [
        base.Course(
            name="Tierra Rejada - Back 9",
            id=23231,
            is_par_3=False,
            is_9_hole=True,
            is_par_70_plus=False,
            booking_url="https://tierrarejadapubpp.ezlinksgolf.com/index.html#/search",
        ),
        base.Course(
            name="Tierra Rejada",
            id=19894,
            is_par_3=False,
            is_9_hole=False,
            is_par_70_plus=True,
            booking_url="https://tierrarejadapubpp.ezlinksgolf.com/index.html#/search",
        ),
    ]


class LACityClient(EZLinksBaseClient):
    base_url = "https://cityofla.ezlinksgolf.com/api"
    courses = [
        base.Course(
            name="Harding",
            id=5997,
            is_par_3=False,
            is_9_hole=False,
            is_par_70_plus=True,
            booking_url="https://cityofla.ezlinksgolf.com/index.html#/preSearch",
        ),
        base.Course(
            name="Wilson",
            id=5998,
            is_par_3=False,
            is_9_hole=False,
            is_par_70_plus=True,
            booking_url="https://cityofla.ezlinksgolf.com/index.html#/preSearch",
        ),
        base.Course(
            name="Hansen Dam",
            id=5995,
            is_par_3=False,
            is_9_hole=False,
            is_par_70_plus=True,
            booking_url="https://cityofla.ezlinksgolf.com/index.html#/preSearch",
        ),
        base.Course(
            name="Hansen Dam - Back 9",
            id=23128,
            is_par_3=False,
            is_9_hole=True,
            is_par_70_plus=False,
            booking_url="https://cityofla.ezlinksgolf.com/index.html#/preSearch",
        ),
        base.Course(
            name="Harbor Park",
            id=5996,
            is_par_3=False,
            is_9_hole=True,
            is_par_70_plus=False,
            booking_url="https://cityofla.ezlinksgolf.com/index.html#/preSearch",
        ),
        base.Course(
            name="Los Feliz",
            id=17679,
            is_par_3=True,
            is_9_hole=True,
            is_par_70_plus=False,
            booking_url="https://cityofla.ezlinksgolf.com/index.html#/preSearch",
        ),
        base.Course(
            name="Penmar",
            id=6171,
            is_par_3=False,
            is_9_hole=True,
            is_par_70_plus=False,
            booking_url="https://cityofla.ezlinksgolf.com/index.html#/preSearch",
        ),
        base.Course(
            name="Rancho Park",
            id=6204,
            is_par_3=False,
            is_9_hole=False,
            is_par_70_plus=True,
            booking_url="https://cityofla.ezlinksgolf.com/index.html#/preSearch",
        ),
        base.Course(
            name="Rancho Park - Back 9",
            id=23129,
            is_par_3=False,
            is_9_hole=True,
            is_par_70_plus=False,
            booking_url="https://cityofla.ezlinksgolf.com/index.html#/preSearch",
        ),
        base.Course(
            name="Rancho Park Par-3",
            id=6205,
            is_par_3=True,
            is_9_hole=True,
            is_par_70_plus=False,
            booking_url="https://cityofla.ezlinksgolf.com/index.html#/preSearch",
        ),
        base.Course(
            name="Roosevelt",
            id=6226,
            is_par_3=False,
            is_9_hole=True,
            is_par_70_plus=False,
            booking_url="https://cityofla.ezlinksgolf.com/index.html#/preSearch",
        ),
        base.Course(
            name="Balboa",
            id=6264,
            is_par_3=False,
            is_9_hole=False,
            is_par_70_plus=True,
            booking_url="https://cityofla.ezlinksgolf.com/index.html#/preSearch",
        ),
        base.Course(
            name="Balboa - Back 9",
            id=23131,
            is_par_3=False,
            is_9_hole=True,
            is_par_70_plus=False,
            booking_url="https://cityofla.ezlinksgolf.com/index.html#/preSearch",
        ),
        base.Course(
            name="Encino",
            id=6263,
            is_par_3=False,
            is_9_hole=False,
            is_par_70_plus=True,
            booking_url="https://cityofla.ezlinksgolf.com/index.html#/preSearch",
        ),
        base.Course(
            name="Encino - Back 9",
            id=23130,
            is_par_3=False,
            is_9_hole=True,
            is_par_70_plus=False,
            booking_url="https://cityofla.ezlinksgolf.com/index.html#/preSearch",
        ),
        base.Course(
            name="Woodley Lakes",
            id=6380,
            is_par_3=False,
            is_9_hole=False,
            is_par_70_plus=True,
            booking_url="https://cityofla.ezlinksgolf.com/index.html#/preSearch",
        ),
        base.Course(
            name="Woodley Lakes - Back 9",
            id=23132,
            is_par_3=False,
            is_9_hole=True,
            is_par_70_plus=False,
            booking_url="https://cityofla.ezlinksgolf.com/index.html#/preSearch",
        ),
    ]
