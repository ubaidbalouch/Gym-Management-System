"""Domain model for individual payment transactions."""

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Payment:
    """Represents a single payment transaction against a member fee."""

    payment_id: int
    fee_id: int
    amount: float
    payment_method: str
    notes: str
    payment_date: str

    @classmethod
    def from_row(cls, row: Mapping[str, object]) -> "Payment":
        return cls(
            payment_id=int(row["payment_id"]),
            fee_id=int(row["fee_id"]),
            amount=float(row["amount"] or 0.0),
            payment_method=str(row["payment_method"] or "Cash"),
            notes=str(row["notes"] or ""),
            payment_date=str(row["payment_date"] or ""),
        )
