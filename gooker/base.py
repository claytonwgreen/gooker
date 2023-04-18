from typing import Union
from abc import ABC, abstractmethod
import uuid
import datetime

import pendulum
from pendulum.date import Date
from pendulum.datetime import DateTime
from pendulum.time import Time
from pydantic import BaseModel, validator
from httpx import AsyncClient


class Course(BaseModel):
    name: str
    id: Union[int, str]
    is_par_3: bool
    is_9_hole: bool
    is_par_70_plus: bool

    def __eq__(self, other):
        return (
            isinstance(other, Course)
            and self.name == other.name
            and isinstance(other.id, type(self.id))
            and self.id == other.id
        )


class TeeTime(BaseModel):
    course: Course
    tee_time: DateTime
    num_golfers: int
    price: float

    @validator("tee_time")
    def must_be_pendulum_datetime(cls, val):
        if isinstance(val, datetime.datetime):
            return pendulum.instance(val)
        return val

    def __eq__(self, other):
        return (
            isinstance(other, TeeTime)
            and self.course == other.course
            and self.tee_time == other.tee_time
        )


class TeeTimes(BaseModel):
    tee_times: dict[Date, dict[str, list[TeeTime]]] = {}

    def add_tee_time(self, tee_time: TeeTime):
        if tee_time.tee_time.date() not in self.tee_times:
            self.tee_times[tee_time.tee_time.date()] = {}
        if tee_time.course.name not in self.tee_times[tee_time.tee_time.date()]:
            self.tee_times[tee_time.tee_time.date()][tee_time.course.name] = []
        self.tee_times[tee_time.tee_time.date()][tee_time.course.name].append(tee_time)

    def create_tee_time_message(self) -> str:
        msg = "Tee times:"
        for date, course_map in sorted(self.tee_times.items(), key=lambda x: x[0]):
            msg += f"\n{date}:\n"
            for course, tee_times in course_map.items():
                msg += f"\t{course}:\n"
                for tee_time in sorted(
                    tee_times, key=lambda tee_time: tee_time.tee_time.time()
                ):
                    msg += f"\t\t{tee_time.tee_time.time().format('h:mm A')}, ${int(tee_time.price)}, {tee_time.num_golfers} players\n"

        return msg


class TeeTimeSearchParams(BaseModel):
    start_date: Date
    start_time: Time | None
    end_date: Date
    end_time: Time | None
    courses: list[str] | None
    par_70_plus: bool
    eighteen_holes: bool
    nine_holes: bool
    min_players: int = 4
    earliest_time: Time | None = None
    latest_time: Time | None = None
    max_price: int | None = None

    @validator("start_date", "end_date")
    def must_be_pendulum_date(cls, val):
        if isinstance(val, datetime.date):
            return pendulum.date(val.year, val.month, val.day)
        return val

    @validator("start_time", "end_time", "earliest_time", "latest_time")
    def must_be_pendulum_time(cls, val):
        if isinstance(val, datetime.time):
            return pendulum.time(val.hour, val.minute, val.second)
        return val

    def create_search_param_message(self) -> str:
        msg = "Search Parameters:"
        msg += f"\n\tStart Date: {self.start_date.format('ddd MMM Do')}"
        if self.start_time:
            msg += f"\n\tStart Time: {self.start_time.format('h:mm A')}"
        msg += f"\n\tEnd Date: {self.end_date.format('ddd MMM Do')}"
        if self.end_time:
            msg += f"\n\tEnd Time: {self.end_time.format('h:mm A')}"
        if self.courses:
            msg += f"\n\tCourses: {self.courses}"
        if self.par_70_plus:
            msg += f"\n\tPar 70+: {self.par_70_plus}"
        if self.eighteen_holes:
            msg += f"\n\t18 Holes: {self.eighteen_holes}"
        if self.nine_holes:
            msg += f"\n\t9 Holes: {self.nine_holes}"
        if self.min_players:
            msg += f"\n\tMin Players: {self.min_players}"
        if self.earliest_time:
            msg += f"\n\tEarliest Time: {self.earliest_time.format('h:mm A')}"
        if self.latest_time:
            msg += f"\n\tLatest Time: {self.latest_time.format('h:mm A')}"
        if self.max_price:
            msg += f"\n\tMax Price: ${self.max_price}"

        return msg


class TeeTimeSearch(BaseModel):
    id: uuid.UUID
    notification_method: str
    notification_destination: list[str]
    search_params: TeeTimeSearchParams


class TeeTimeClient(ABC):
    client: AsyncClient
    base_url: str
    courses: list[Course]
    default_earliest_time: Time = Time(5, 0)  # 5am
    default_latest_time: Time = Time(19, 0)  # 7pm

    def __init__(self):
        self.client = AsyncClient(
            base_url=self.base_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/110.0"
            },
            verify=False,
        )

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    @abstractmethod
    async def get_tee_times(
        self,
        courses: list[Course],
        date: Date,
        earliest_time: Time | None = None,
        latest_time: Time | None = None,
        min_players: int = 4,
        max_price: int | None = None,
    ) -> list[TeeTime]:
        ...
