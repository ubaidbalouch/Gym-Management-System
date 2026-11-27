"""SQLite repository for dashboard KPIs and payment breakdown statistics."""

from dataclasses import dataclass

from src.common.database import DatabaseConnection
from src.features.fees.fee_repository import FeeRepository


@dataclass(frozen=True)
class DashboardStats:
    """Aggregated gym metrics displayed on the dashboard."""

    total_members: int
    pending_count: int
    total_fees: float
    total_paid: float
    total_pending: float
    status_breakdown: dict[str, int]


class DashboardRepository:
    """Queries aggregated statistics and exports summary reports."""

    def __init__(self, db: DatabaseConnection) -> None:
        self.db = db
        self.fee_repo = FeeRepository(db)

    def get_stats(self) -> DashboardStats:
        """Compute member count, pending fee count, PKR totals, and status counts."""
        with self.db.session() as conn:
            total_members = int(conn.execute("SELECT COUNT(*) FROM members").fetchone()[0] or 0)
            totals = conn.execute(
                "SELECT COALESCE(SUM(total_amount), 0), COALESCE(SUM(paid_amount), 0) FROM member_fees"
            ).fetchone()
            total_fees = float(totals[0] or 0.0)
            total_paid = float(totals[1] or 0.0)

            pending_count = int(
                conn.execute(
                    "SELECT COUNT(*) FROM member_fees WHERE COALESCE(payment_status, 'Pending') != 'Paid'"
                ).fetchone()[0]
                or 0
            )

            breakdown_rows = conn.execute(
                """
                SELECT COALESCE(payment_status, 'Pending') AS status, COUNT(*) AS cnt
                FROM member_fees
                GROUP BY COALESCE(payment_status, 'Pending')
                """
            ).fetchall()
            breakdown = {str(row["status"]): int(row["cnt"]) for row in breakdown_rows}

        return DashboardStats(
            total_members=total_members,
            pending_count=pending_count,
            total_fees=total_fees,
            total_paid=total_paid,
            total_pending=max(0.0, total_fees - total_paid),
            status_breakdown=breakdown,
        )

    def export_payment_report(self, filename: str) -> tuple[bool, str]:
        """Export full payment report to Excel."""
        return self.fee_repo.export_all_fees_excel(filename)
