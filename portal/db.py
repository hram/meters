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
        con.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS meter_assignments (
                service TEXT NOT NULL,
                meter_id TEXT NOT NULL,
                property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
                PRIMARY KEY (service, meter_id)
            )
        """)
        for service in _SERVICES:
            con.execute(
                "INSERT INTO service_settings (service) VALUES (?) ON CONFLICT DO NOTHING",
                (service,),
            )


# ── Properties ────────────────────────────────────────────────────────────────

def get_properties() -> list[dict]:
    with _conn() as con:
        rows = con.execute("SELECT id, name FROM properties ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def create_property(name: str) -> dict:
    with _conn() as con:
        cur = con.execute("INSERT INTO properties (name) VALUES (?)", (name,))
        return {"id": cur.lastrowid, "name": name}


def update_property(prop_id: int, name: str) -> dict:
    with _conn() as con:
        con.execute("UPDATE properties SET name = ? WHERE id = ?", (name, prop_id))
    return {"id": prop_id, "name": name}


def delete_property(prop_id: int) -> None:
    with _conn() as con:
        con.execute("DELETE FROM properties WHERE id = ?", (prop_id,))


# ── Meter assignments ─────────────────────────────────────────────────────────

def get_assignments() -> dict[tuple[str, str], int]:
    """Returns {(service, meter_id): property_id}."""
    with _conn() as con:
        rows = con.execute(
            "SELECT service, meter_id, property_id FROM meter_assignments"
        ).fetchall()
    return {(row["service"], row["meter_id"]): row["property_id"] for row in rows}


def set_assignment(service: str, meter_id: str, property_id: int) -> None:
    with _conn() as con:
        con.execute(
            """
            INSERT INTO meter_assignments (service, meter_id, property_id) VALUES (?, ?, ?)
            ON CONFLICT(service, meter_id) DO UPDATE SET property_id = excluded.property_id
            """,
            (service, meter_id, property_id),
        )


def delete_assignment(service: str, meter_id: str) -> None:
    with _conn() as con:
        con.execute(
            "DELETE FROM meter_assignments WHERE service = ? AND meter_id = ?",
            (service, meter_id),
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
