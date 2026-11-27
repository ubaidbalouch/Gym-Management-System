"""SQLite repository for fee types, fee assignment, and fee queries."""

from datetime import date
from typing import Optional

from src.common.database import DatabaseConnection
from src.common.utils import export_query_to_excel
from .fee_model import FeeType, MemberFee

_BASE_FEE_SELECT = """
    SELECT
        mf.fee_id,
        mf.member_id,
        COALESCE(m.name, 'Unknown') AS member_name,
        mf.fee_type_id,
        COALESCE(ft.fee_name, 'Unknown') AS fee_name,
        mf.total_amount,
        COALESCE(mf.paid_amount, 0) AS paid_amount,
        COALESCE(mf.payment_status, 'Pending') AS payment_status,
        mf.created_date,
        mf.last_payment_date,
        mf.notes,
        (
            SELECT p.payment_method
            FROM payments p
            WHERE p.fee_id = mf.fee_id
            ORDER BY p.payment_id DESC
            LIMIT 1
        ) AS last_payment_method
    FROM member_fees mf
    LEFT JOIN fee_types ft ON mf.fee_type_id = ft.fee_type_id
    LEFT JOIN members m ON mf.member_id = m.member_id
"""


class FeeRepository:
    """Data access methods for fee types and assigned member fees."""

    def __init__(self, db: DatabaseConnection) -> None:
        self.db = db

    def get_fee_types(self) -> list[FeeType]:
        """Return all available fee categories."""
        with self.db.session() as conn:
            rows = conn.execute(
                "SELECT fee_type_id, fee_name FROM fee_types ORDER BY fee_type_id ASC"
            ).fetchall()
        return [FeeType.from_row(row) for row in rows]

    def assign_fee(
        self,
        member_id: int,
        fee_type_id: int,
        amount: float,
        assigned_date: Optional[str] = None,
        notes: str = "",
    ) -> int:
        """Assign a fee to a member and return the newly created fee_id."""
        if amount <= 0:
            raise ValueError("Amount must be greater than 0!")

        with self.db.session() as conn:
            member_row = conn.execute(
                "SELECT member_id FROM members WHERE member_id = ?", (member_id,)
            ).fetchone()
            if not member_row:
                raise ValueError(f"Member ID {member_id} does not exist!")

            fee_type_row = conn.execute(
                "SELECT fee_type_id FROM fee_types WHERE fee_type_id = ?", (fee_type_id,)
            ).fetchone()
            if not fee_type_row:
                raise ValueError(f"Fee Type ID {fee_type_id} does not exist!")

            cursor = conn.execute(
                """
                INSERT INTO member_fees
                    (member_id, fee_type_id, total_amount, paid_amount, payment_status, created_date, notes)
                VALUES (?, ?, ?, 0, 'Pending', ?, ?)
                """,
                (
                    member_id,
                    fee_type_id,
                    float(amount),
                    assigned_date or date.today().isoformat(),
                    notes.strip(),
                ),
            )
            return int(cursor.lastrowid)

    def get_all_fees(self, status_filter: Optional[str] = None) -> list[MemberFee]:
        """Return all member fees, optionally filtered by payment_status."""
        query = _BASE_FEE_SELECT
        params: list[object] = []
        if status_filter and status_filter.lower() != "all":
            query += " WHERE LOWER(COALESCE(mf.payment_status, 'Pending')) = LOWER(?)"
            params.append(status_filter)
        query += " ORDER BY mf.fee_id DESC"

        with self.db.session() as conn:
            rows = conn.execute(query, params).fetchall()
        return [MemberFee.from_row(row) for row in rows]

    def get_member_fees(self, member_id: int) -> list[MemberFee]:
        """Return all fees assigned to a specific member."""
        query = f"{_BASE_FEE_SELECT} WHERE mf.member_id = ? ORDER BY mf.fee_id DESC"
        with self.db.session() as conn:
            rows = conn.execute(query, (member_id,)).fetchall()
        return [MemberFee.from_row(row) for row in rows]

    def export_member_fees_excel(self, member_id: int, filename: str) -> tuple[bool, str]:
        """Export a single member's fees to Excel."""
        query = """
            SELECT
                m.name AS 'Member Name',
                mf.fee_id AS 'Fee ID',
                ft.fee_name AS 'Type',
                mf.total_amount AS 'Total',
                COALESCE(mf.paid_amount, 0) AS 'Paid',
                (mf.total_amount - COALESCE(mf.paid_amount, 0)) AS 'Pending',
                COALESCE(mf.payment_status, 'Pending') AS 'Status',
                (
                    SELECT payment_method FROM payments
                    WHERE fee_id = mf.fee_id
                    ORDER BY payment_id DESC LIMIT 1
                ) AS 'Method'
            FROM member_fees mf
            LEFT JOIN fee_types ft ON mf.fee_type_id = ft.fee_type_id
            LEFT JOIN members m ON mf.member_id = m.member_id
            WHERE mf.member_id = ?
            ORDER BY mf.fee_id DESC
        """
        return export_query_to_excel(
            self.db,
            query,
            filename,
            params=(member_id,),
            fill_na_columns=("Method",),
        )

    def export_all_fees_excel(self, filename: str) -> tuple[bool, str]:
        """Export all member fees and payment statuses to Excel."""
        query = """
            SELECT
                m.name AS 'Member Name',
                ft.fee_name AS 'Fee Type',
                (
                    SELECT payment_method FROM payments
                    WHERE fee_id = mf.fee_id
                    ORDER BY payment_id DESC LIMIT 1
                ) AS 'Payment Method',
                COALESCE(mf.payment_status, 'Pending') AS 'Status',
                mf.created_date AS 'Fee Date',
                mf.total_amount AS 'Total Amount',
                COALESCE(mf.paid_amount, 0) AS 'Paid Amount',
                (mf.total_amount - COALESCE(mf.paid_amount, 0)) AS 'Pending'
            FROM member_fees mf
            LEFT JOIN fee_types ft ON mf.fee_type_id = ft.fee_type_id
            LEFT JOIN members m ON mf.member_id = m.member_id
            ORDER BY mf.fee_id DESC
        """
        return export_query_to_excel(
            self.db,
            query,
            filename,
            fill_na_columns=("Payment Method",),
        )
