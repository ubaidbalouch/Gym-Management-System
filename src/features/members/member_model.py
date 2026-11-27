"""Domain model for gym members."""

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Member:
    """Represents a registered gym member."""

    member_id: int
    name: str
    phone: str
    registration_date: str

    @classmethod
    def from_row(cls, row: Mapping[str, object]) -> "Member":
        return cls(
            member_id=int(row["member_id"]),
            name=str(row["name"] or ""),
            phone=str(row["phone"] or ""),
            registration_date=str(row["registration_date"] or ""),
        )
