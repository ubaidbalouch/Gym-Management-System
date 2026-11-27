"""SQLite connection manager with safe PyInstaller path resolution and transactions."""

from contextlib import contextmanager
import os
import shutil
import sqlite3
import sys
from typing import Iterator, Optional


def resolve_database_path(db_path: Optional[str] = None) -> str:
    """Resolve a writable database path for development and PyInstaller builds."""
    if db_path:
        if db_path == ":memory:" or os.path.isabs(db_path):
            return db_path
        return os.path.abspath(db_path)

    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        target_db = os.path.join(exe_dir, "gym.db")
        if not os.path.exists(target_db):
            bundled_db = os.path.join(getattr(sys, "_MEIPASS", exe_dir), "gym.db")
            if os.path.exists(bundled_db):
                shutil.copy2(bundled_db, target_db)
        return target_db

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    return os.path.join(project_root, "gym.db")


class DatabaseConnection:
    """Manages SQLite connections with foreign-key enforcement and transactions."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = resolve_database_path(db_path)

    def connect(self) -> sqlite3.Connection:
        """Open a SQLite connection configured with Row factory and foreign keys."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        """Yield a transactional SQLite connection that commits or rolls back safely."""
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
