"""
database.py
SQLite storage for bus information.

Table: buses
    bus_number  TEXT PRIMARY KEY   e.g. KL-15-1234
    camera_id   TEXT               e.g. camera_01
    route       TEXT               e.g. Aluva → Ernakulam
    capacity    INTEGER
    status      TEXT               'active' or 'inactive'
"""

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "bus.db"

SAMPLE_BUSES = [
    ("KL-15-1234", "camera_01", "Aluva → Ernakulam", 40, "active"),
    ("KL-07-5678", "camera_02", "Angamaly → Ernakulam", 45, "active"),
    ("KL-01-9999", "camera_03", "Thrissur → Ernakulam", 50, "active"),
]


import re

def normalize_bus_number(text: str) -> str:
    """
    Accepts messy input: 'kl151234', 'kl-15-1234', 'KL 15 1234', 'kl_15_1234'
    and returns the standard format 'KL-15-1234'.

    Expected pattern: 2 letters (state code) + 2 digits (RTO code) + 4 digits (number)
    e.g. KL 15 1234 -> KL-15-1234

    If the input doesn't match that pattern, it's returned as-is
    (uppercased, trimmed) so lookups still work for anything already
    correctly formatted or unusual.
    """
    raw = text.strip().upper()
    compact = re.sub(r"[\s\-_]", "", raw)  # remove spaces, dashes, underscores

    match = re.match(r"^([A-Z]{2})(\d{2})(\d{3,4})$", compact)
    if match:
        state, rto, number = match.groups()
        return f"{state}-{rto}-{number}"

    return raw


def _connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn


def init_db():
    """Create the table if missing and add the sample buses if the table is empty."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS buses (
                bus_number TEXT PRIMARY KEY,
                camera_id  TEXT NOT NULL,
                route      TEXT NOT NULL,
                capacity   INTEGER NOT NULL,
                status     TEXT NOT NULL DEFAULT 'active'
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM buses").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO buses VALUES (?, ?, ?, ?, ?)", SAMPLE_BUSES
            )


def get_bus(bus_number: str):
    """Returns a dict for the bus, or None if not found."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM buses WHERE bus_number = ?",
            (normalize_bus_number(bus_number),),
        ).fetchone()
    return dict(row) if row else None


def list_buses():
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM buses ORDER BY bus_number").fetchall()
    return [dict(r) for r in rows]

def search_by_route(query: str):
    """
    Direction-flexible, case-insensitive route search.
    'Ernakulam Angamaly' matches 'Angamaly → Ernakulam'.
    Returns a list of matching bus dicts (possibly empty).
    """
    words = [w.strip().lower() for w in query.split() if w.strip()]
    if not words:
        return []

    with _connect() as conn:
        rows = conn.execute("SELECT * FROM buses ORDER BY bus_number").fetchall()

    results = []
    for row in rows:
        route_lower = row["route"].lower()
        if all(word in route_lower for word in words):
            results.append(dict(row))
    return results