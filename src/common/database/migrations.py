"""Idempotent SQLite schema creation and default fee-type seeding."""

import sqlite3

from .db_connection import DatabaseConnection

DEFAULT_FEE_TYPES = (
    "Monthly Fee",
    "Admission Fee",
    "Personal Training",
    "Supplement Fee",
)


def initialize_schema(db: DatabaseConnection) -> None:
    """Create required tables, apply column migrations, and seed default fee types."""
    with db.session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS members (
                member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT,
                registration_date TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fee_types (
                fee_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
                fee_name TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS member_fees (
                fee_id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER,
                fee_type_id INTEGER,
                total_amount REAL,
                paid_amount REAL DEFAULT 0,
                payment_status TEXT,
                created_date TEXT,
                notes TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                fee_id INTEGER,
                amount REAL,
                payment_method TEXT,
                notes TEXT,
                payment_date TEXT
            )
            """
        )

        try:
            cursor.execute("ALTER TABLE member_fees ADD COLUMN last_payment_date TEXT")
        except sqlite3.OperationalError:
            pass

        cursor.execute("SELECT fee_name FROM fee_types")
        existing_types = {row["fee_name"] for row in cursor.fetchall()}
        for fee_name in DEFAULT_FEE_TYPES:
            if fee_name not in existing_types:
                cursor.execute("INSERT INTO fee_types (fee_name) VALUES (?)", (fee_name,))
