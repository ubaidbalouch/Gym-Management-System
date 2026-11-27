"""SQLite repository for searching members and fetching comprehensive fee summaries."""

from dataclasses import dataclass
from typing import Optional

from src.common.database import DatabaseConnection
from src.features.fees.fee_model import MemberFee
from src.features.fees.fee_repository import FeeRepository
from src.features.members.member_model import Member
from src.features.members.member_repository import MemberRepository


@dataclass(frozen=True)
class MemberComprehensiveDetails:
    """Aggregated profile and financial summary for a single member."""

    member: Member
    fees: list[MemberFee]
    total_fees: float
    paid_amount: float
    pending_amount: float
    overall_status: str


class SearchRepository:
    """Data access methods for member search and comprehensive reports."""

    def __init__(self, db: DatabaseConnection) -> None:
        self.db = db
        self.member_repo = MemberRepository(db)
        self.fee_repo = FeeRepository(db)

    def search_members(self, term: str) -> list[Member]:
        """Search members by ID, name, or phone substring."""
        cleaned = term.strip()
        if not cleaned:
            return self.member_repo.get_all()

        like_pattern = f"%{cleaned}%"
        with self.db.session() as conn:
            rows = conn.execute(
                """
                SELECT member_id, name, phone, registration_date
                FROM members
                WHERE name LIKE ? OR phone LIKE ? OR CAST(member_id AS TEXT) LIKE ?
                ORDER BY member_id DESC
                """,
                (like_pattern, like_pattern, like_pattern),
            ).fetchall()
        return [Member.from_row(row) for row in rows]

    def get_member_comprehensive_details(
        self, member_id: int
    ) -> Optional[MemberComprehensiveDetails]:
        """Fetch member profile, all fees, and aggregated payment totals."""
        member = self.member_repo.get_by_id(member_id)
        if not member:
            return None

        fees = self.fee_repo.get_member_fees(member_id)
        if not fees:
            return MemberComprehensiveDetails(
                member=member,
                fees=[],
                total_fees=0.0,
                paid_amount=0.0,
                pending_amount=0.0,
                overall_status="No Fees",
            )

        total_fees = sum(f.total_amount for f in fees)
        paid_amount = sum(f.paid_amount for f in fees)
        pending_amount = max(0.0, total_fees - paid_amount)

        if pending_amount <= 0:
            overall_status = "Paid"
        elif paid_amount > 0:
            overall_status = "Partial"
        else:
            overall_status = "Pending"

        return MemberComprehensiveDetails(
            member=member,
            fees=fees,
            total_fees=total_fees,
            paid_amount=paid_amount,
            pending_amount=pending_amount,
            overall_status=overall_status,
        )
