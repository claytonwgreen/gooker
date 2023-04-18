import sqlite3
from contextlib import AbstractContextManager
from typing import Union
from types import TracebackType
from functools import partial
from pathlib import Path
import logging
import json
import uuid

import pendulum
from pendulum.date import Date
from pendulum.time import Time
from pendulum.datetime import DateTime

from gooker import base


DB_INIT_PATH = Path(__file__).parent.parent / "db" / "init.sql"
MIGRATION_PATH = Path(__file__).parent.parent / "db" / "migrations"

logger = logging.getLogger("database")


def adapt_date_time(val: Union[Date, Time, DateTime]):
    """Adapt date/time values."""
    return val.isoformat()


sqlite3.register_adapter(Date, adapt_date_time)
sqlite3.register_adapter(Time, adapt_date_time)
sqlite3.register_adapter(DateTime, adapt_date_time)


def convert_date_time(_type: Union[type[Date], type[Time], type[DateTime]], val: bytes):
    """Convert date/time values."""
    return _type.fromisoformat(val.decode())


sqlite3.register_converter("date", partial(convert_date_time, Date))
sqlite3.register_converter("time", partial(convert_date_time, Time))
sqlite3.register_converter("datetime", partial(convert_date_time, DateTime))

sqlite3.register_adapter(base.TeeTimeSearchParams, lambda x: x.json())
sqlite3.register_converter("tee_time_search_params", base.TeeTimeSearchParams.parse_raw)
sqlite3.register_adapter(base.TeeTime, lambda x: x.json())
sqlite3.register_converter("tee_time", base.TeeTime.parse_raw)
sqlite3.register_adapter(list, json.dumps)
sqlite3.register_converter("text_list", json.loads)
sqlite3.register_adapter(uuid.UUID, str)
sqlite3.register_converter("uuid", lambda x: uuid.UUID(x.decode()))


class DBClient(AbstractContextManager):
    con: sqlite3.Connection

    def __enter__(self):
        self.con = sqlite3.connect(
            Path(__file__).parent.parent / ".gooker.db",
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        with self.con as transaction:
            transaction.executescript(DB_INIT_PATH.read_text())
            cursor = transaction.execute("select max(name) from __migrations__;")
            cur_migration = cursor.fetchone()[0]

        for path in sorted(MIGRATION_PATH.glob("*.sql")):
            with self.con as transaction:
                if not path.is_file():
                    continue

                if cur_migration and str(path) <= cur_migration:
                    continue

                logger.info(f"Applying {path.stem}...")
                transaction.executescript(path.read_text())
                transaction.execute(
                    "insert into __migrations__ (name, applied_at) values (?, ?)",
                    (path.stem, pendulum.now().date()),
                )

        return self

    def __exit__(
        self,
        __exc_type: type[BaseException] | None,
        __exc_value: BaseException | None,
        __traceback: TracebackType | None,
    ) -> bool | None:
        self.con.close()
        return super().__exit__(__exc_type, __exc_value, __traceback)

    def get_current_tee_time_searches(self) -> list[base.TeeTimeSearch]:
        res = self.con.execute(
            "select id, notification_method, notification_destination, search_params from tee_time_search"
        )
        return [
            base.TeeTimeSearch(
                id=row[0],
                notification_method=row[1],
                notification_destination=row[2],
                search_params=row[3],
            )
            for row in res.fetchall()
        ]

    def insert_tee_time_search(self, search: base.TeeTimeSearch):
        with self.con as transaction:
            transaction.execute(
                """
                insert into tee_time_search
                (
                    id,
                    notification_method,
                    notification_destination,
                    search_params
                )
                values (?, ?, ?, ?)
                """,
                (
                    search.id,
                    search.notification_method,
                    search.notification_destination,
                    search.search_params,
                ),
            )

    def delete_tee_time_search(self, search: base.TeeTimeSearch):
        with self.con as transaction:
            transaction.execute(
                """
                delete from tee_time_search
                where id = ?
                """,
                (search.id,),
            )

    def get_current_tee_time_search_results(self, id: uuid.UUID) -> list[base.TeeTime]:
        res = self.con.execute(
            "select tee_time from tee_time_search_result where search_id = ?", (id,)
        )
        return [row[0] for row in res.fetchall()]

    def insert_tee_time_search_results(
        self, id: uuid.UUID, tee_times: list[base.TeeTime]
    ):
        with self.con as transaction:
            transaction.executemany(
                """
                insert into tee_time_search_result
                (search_id,tee_time)
                values (?, ?)
                """,
                ((id, tee_time) for tee_time in tee_times),
            )

    def delete_tee_time_search_results(
        self, id: uuid.UUID, tee_times: list[base.TeeTime]
    ):
        with self.con as transaction:
            transaction.executemany(
                """
                delete from tee_time_search_result
                where search_id = ? and tee_time = ?
                """,
                ((id, tee_time) for tee_time in tee_times),
            )
