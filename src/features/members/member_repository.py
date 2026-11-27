"""SQLite repository for member CRUD operations."""

from datetime import date
from typing import Optional

from src.common.database import DatabaseConnection
from .member_model import Member


class MemberRepository:
    """Data access methods for gym members."""

    def __init__(self, db: DatabaseConnection) -> None:
        self.db = db

    def get_all(self) -> list[Member]:
        """Return all members ordered by newest first."""
        with self.db.session() as conn:
            rows = conn.execute(
                "SELECT member_id, name, phone, registration_date FROM members ORDER BY member_id DESC"
            ).fetchall()
        return [Member.from_row(row) for row in rows]

    def get_by_id(self, member_id: int) -> Optional[Member]:
        """Return a single member by ID, or None if not found."""
        with self.db.session() as conn:
            row = conn.execute(
                "SELECT member_id, name, phone, registration_date FROM members WHERE member_id = ?",
                (member_id,),
            ).fetchone()
        return Member.from_row(row) if row else None

    def create(self, name: str, phone: str) -> int:
        """Insert a new member and return the assigned member_id."""
        with self.db.session() as conn:
            cursor = conn.execute(
                "INSERT INTO members (name, phone, registration_date) VALUES (?, ?, ?)",
                (name.strip(), phone.strip(), date.today().isoformat()),
            )
            return int(cursor.lastrowid)

    def update(self, member_id: int, name: str, phone: str) -> bool:
        """Update an existing member's name and phone."""
        with self.db.session() as conn:
            cursor = conn.execute(
                "UPDATE members SET name = ?, phone = ? WHERE member_id = ?",
                (name.strip(), phone.strip(), member_id),
            )
            return cursor.rowcount > 0

    def delete(self, member_id: int) -> bool:
        """Delete a member along with their assigned fees and payment records."""
        with self.db.session() as conn:
            conn.execute(
                """
                DELETE FROM payments
                WHERE fee_id IN (SELECT fee_id FROM member_fees WHERE member_id = ?)
                """,
                (member_id,),
            )
            conn.execute("DELETE FROM member_fees WHERE member_id = ?", (member_id,))
            cursor = conn.execute("DELETE FROM members WHERE member_id = ?", (member_id,))
            return cursor.rowcount > 0

    def delete_all(self) -> None:
        """Permanently delete all payments, fees, and members."""
        with self.db.session() as conn:
            conn.execute("DELETE FROM payments")
            conn.execute("DELETE FROM member_fees")
            conn.execute("DELETE FROM members")
