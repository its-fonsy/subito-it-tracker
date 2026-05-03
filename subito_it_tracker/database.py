import os
import sqlite3
from pathlib import Path
from .subito import SubitoItem, SubitoQuery


def _get_db_path() -> str:
    xdg = os.environ.get("XDG_DATA_HOME")
    data_dir = Path(xdg if xdg else Path.home() / ".local/share") / "subito-it-tracker"
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir / "subito_tracker.sqlite3")


class Database:
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path if db_path else _get_db_path()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS queries (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                title     TEXT NOT NULL UNIQUE,
                text      TEXT NOT NULL UNIQUE,
                min_price REAL,
                max_price REAL
            );

            CREATE TABLE IF NOT EXISTS items (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER NOT NULL REFERENCES queries(id),
                title    TEXT,
                price    REAL,
                date     TEXT,
                geo      TEXT,
                url      TEXT,
                tracked  INTEGER DEFAULT 0,
                UNIQUE(title, price, date, geo, url)
            );
            """
        )
        self.conn.commit()

    def insert_query(self, query: SubitoQuery) -> int:
        cur = self.conn.execute(
            "INSERT INTO queries (title, text, min_price, max_price) VALUES (?, ?, ?, ?)",
            (query.title, query.text, query.min_price, query.max_price)
        )
        self.conn.commit()
        return cur.lastrowid

    def remove_query(self, query_id: int) -> None:
        self.conn.execute("DELETE FROM items WHERE query_id = ?", (query_id,))
        self.conn.execute("DELETE FROM queries WHERE id = ?", (query_id,))
        self.conn.commit()

    def get_all_queries(self) -> list[SubitoQuery]:

        query_list = []
        rows = self.conn.execute("SELECT * FROM queries").fetchall()

        for row in rows:
            r = dict(row)
            query = SubitoQuery()
            query.from_dict(r)
            query_list.append(query)

        return query_list

    def get_all_queries_id(self) -> list[int]:

        query_ids = []
        rows = self.conn.execute("SELECT * FROM queries").fetchall()

        for row in rows:
            query_ids.append(row["id"])

        return query_ids

    def get_query(self, query_id: int) -> SubitoQuery | None:

        row = self.conn.execute("SELECT * FROM queries WHERE id = ?",
                                (query_id,)).fetchone()

        if not row:
            return None

        data = dict(row)
        query = SubitoQuery()
        query.from_dict(data)

        return query

    def insert_item(self, item: SubitoItem, query_id: int) -> bool:
        try:
            self.conn.execute(
                """
                INSERT INTO items (query_id, title, price, date, geo, url, tracked)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (query_id, item.title, item.price, item.date,
                 item.geo, item.url, int(item.tracked))
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # UNIQUE constraint hit → duplicate, skip silently
            return False

    def remove_item(self, item_id: int) -> None:
        self.conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        self.conn.commit()

    def get_item_id(self, item: SubitoItem, query_id: int) -> int:
        row = self.conn.execute(
            """SELECT id FROM items WHERE query_id = ? AND title = ?
            AND price = ? AND date = ? AND geo = ? AND url = ?""",
            (query_id, item.title, item.price, item.date, item.geo, item.url)
        ).fetchone()

        return row["id"]

    def get_item(self, item_id: int) -> SubitoItem:
        row = self.conn.execute(
            "SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        return self._row_to_result(row)

    def get_all_item_of_query(self, query_id: int) -> list[SubitoItem]:
        rows = self.conn.execute(
            "SELECT * FROM items WHERE query_id = ?",
            (query_id,)
        ).fetchall()
        return [self._row_to_result(row) for row in rows]

    def get_tracked_items_of_query(self, query_id: int) -> list[SubitoItem]:
        rows = self.conn.execute(
            "SELECT * FROM items WHERE query_id = ? AND tracked = 1",
            (query_id,)
        ).fetchall()
        return [self._row_to_result(row) for row in rows]

    def set_tracked(self, item_id: int, tracked: bool) -> None:
        self.conn.execute(
            "UPDATE items SET tracked = ? WHERE id = ?",
            (int(tracked), item_id)
        )
        self.conn.commit()

    def _row_to_result(self, row: sqlite3.Row) -> SubitoItem:
        result = SubitoItem()
        result.from_dict({
            "title":   row["title"],
            "price":   row["price"],
            "date":    row["date"],
            "geo":     row["geo"],
            "url":     row["url"],
            "tracked": bool(row["tracked"]),
        })
        return result

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
