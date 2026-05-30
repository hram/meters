import sqlite3
import time
from pathlib import Path

from portal.infrastructure.config import settings

_DB_PATH = Path(settings.data_dir) / "portal.sqlite"
_SERVICES = ("pesc", "gaz")


def _conn() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(_DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS service_settings (
                service TEXT PRIMARY KEY,
                auto_submit INTEGER NOT NULL DEFAULT 0
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS scheduler_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT NOT NULL,
                ran_at INTEGER NOT NULL,
                success INTEGER NOT NULL,
                error TEXT
            )
        """)
        for service in _SERVICES:
            con.execute(
                "INSERT INTO service_settings (service) VALUES (?) ON CONFLICT DO NOTHING",
                (service,),
            )


def get_auto_submit(service: str) -> bool:
    with _conn() as con:
        row = con.execute(
            "SELECT auto_submit FROM service_settings WHERE service = ?", (service,)
        ).fetchone()
    return bool(row["auto_submit"]) if row else False


def set_auto_submit(service: str, enabled: bool) -> None:
    with _conn() as con:
        con.execute(
            "UPDATE service_settings SET auto_submit = ? WHERE service = ?",
            (int(enabled), service),
        )


def get_enabled_services() -> list[str]:
    with _conn() as con:
        rows = con.execute(
            "SELECT service FROM service_settings WHERE auto_submit = 1"
        ).fetchall()
    return [row["service"] for row in rows]


def add_log_entry(service: str, *, success: bool, error: str | None = None) -> None:
    with _conn() as con:
        con.execute(
            "INSERT INTO scheduler_log (service, ran_at, success, error) VALUES (?, ?, ?, ?)",
            (service, int(time.time()), int(success), error),
        )


def get_log(limit: int = 100) -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT service, ran_at, success, error FROM scheduler_log ORDER BY ran_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
