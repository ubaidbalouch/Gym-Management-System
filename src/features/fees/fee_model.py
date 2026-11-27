"""Domain models for fee types and assigned member fees."""

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class FeeType:
    """Represents a catalog fee category (e.g. Monthly Fee)."""

    fee_type_id: int
    fee_name: str

    @classmethod
    def from_row(cls, row: Mapping[str, object]) -> "FeeType":
        return cls(
            fee_type_id=int(row["fee_type_id"]),
            fee_name=str(row["fee_name"] or ""),
        )


@dataclass(frozen=True)
class MemberFee:
    """Represents a fee assigned to a member with aggregated payment progress."""

    fee_id: int
    member_id: int
    member_name: str
    fee_type_id: int
    fee_name: str
    total_amount: float
    paid_amount: float
    payment_status: str
    last_payment_method: str
    created_date: str
    last_payment_date: str
    notes: str

    @property
    def pending_amount(self) -> float:
        return max(0.0, self.total_amount - self.paid_amount)

    @classmethod
    def from_row(cls, row: Mapping[str, object]) -> "MemberFee":
        return cls(
            fee_id=int(row["fee_id"]),
            member_id=int(row["member_id"]),
            member_name=str(row.get("member_name") or "Unknown")
            if isinstance(row, dict)
            else str(row["member_name"] or "Unknown")
            if "member_name" in row.keys()
            else "Unknown",
            fee_type_id=int(row["fee_type_id"] or 0),
            fee_name=str(row["fee_name"] or "Unknown"),
            total_amount=float(row["total_amount"] or 0.0),
            paid_amount=float(row["paid_amount"] or 0.0),
            payment_status=str(row["payment_status"] or "Pending"),
            last_payment_method=str(row["last_payment_method"] or "N/A"),
            created_date=str(row["created_date"] or ""),
            last_payment_date=str(row["last_payment_date"] or ""),
            notes=str(row["notes"] or ""),
        )
