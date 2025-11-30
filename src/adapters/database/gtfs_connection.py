"""
GTFS database connection configuration.

This module provides synchronous SQLite connection to the GTFS database.
"""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

# Path to GTFS database
GTFS_DB_PATH = Path(__file__).parent.parent.parent.parent / "gtfs.db"


@contextmanager
def get_gtfs_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager that provides a connection to the GTFS database.

    Yields:
        sqlite3.Connection for database operations
    """
    conn = sqlite3.connect(str(GTFS_DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
