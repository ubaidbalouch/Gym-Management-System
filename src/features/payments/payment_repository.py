"""SQLite repository for recording payments and querying payment history."""

from datetime import date
from typing import Optional

from src.common.database import DatabaseConnection
from src.features.fees.fee_model import MemberFee
from src.features.fees.fee_repository import FeeRepository


class PaymentRepository:
    """Data access methods for fee payments."""

    PAYMENT_METHODS = ("Cash", "Card", "Bank Transfer", "Jazz Cash", "Easy Paisa")

    def __init__(self, db: DatabaseConnection) -> None:
        self.db = db
        self.fee_repo = FeeRepository(db)

    def record_payment(
        self,
        fee_id: int,
        amount: float,
        payment_method: str = "Cash",
        notes: str = "",
        payment_date: Optional[str] = None,
    ) -> str:
        """Record a payment against a fee and update its status atomically.

        Returns the updated payment_status ('Paid', 'Partial', or 'Pending').
        """
        if amount <= 0:
            raise ValueError("Payment amount must be greater than 0!")

        pdate_iso = payment_date or date.today().isoformat()
        method = payment_method.strip() or "Cash"

        with self.db.session() as conn:
            fee_row = conn.execute(
                "SELECT fee_id, total_amount, paid_amount FROM member_fees WHERE fee_id = ?",
                (fee_id,),
            ).fetchone()
            if not fee_row:
                raise ValueError(f"Fee ID {fee_id} does not exist!")

            current_paid = float(fee_row["paid_amount"] or 0.0)
            total_amount = float(fee_row["total_amount"] or 0.0)
            new_paid = current_paid + float(amount)
            new_status = (
                "Paid" if new_paid >= total_amount else ("Partial" if new_paid > 0 else "Pending")
            )

            conn.execute(
                """
                INSERT INTO payments (fee_id, amount, payment_method, notes, payment_date)
                VALUES (?, ?, ?, ?, ?)
                """,
                (fee_id, float(amount), method, notes.strip(), pdate_iso),
            )
            conn.execute(
                """
                UPDATE member_fees
                SET paid_amount = ?, payment_status = ?, last_payment_date = ?
                WHERE fee_id = ?
                """,
                (new_paid, new_status, pdate_iso, fee_id),
            )
            return new_status

    def get_payment_history(self, status_filter: Optional[str] = None) -> list[MemberFee]:
        """Return fee & payment history rows, optionally filtered by status."""
        return self.fee_repo.get_all_fees(status_filter=status_filter)
