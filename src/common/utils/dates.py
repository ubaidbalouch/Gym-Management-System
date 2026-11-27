"""Date parsing and display helpers."""

from datetime import date
from typing import Optional


def today_ddmmyyyy() -> str:
    """Return today's date formatted as DD-MM-YYYY."""
    return date.today().strftime("%d-%m-%Y")


def parse_ddmmyyyy_to_iso(date_text: str) -> Optional[str]:
    """Convert a DD-MM-YYYY string to YYYY-MM-DD, returning None if empty or invalid."""
    cleaned = date_text.strip()
    if not cleaned:
        return None
    parts = cleaned.split("-")
    if len(parts) != 3:
        return None
    try:
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        parsed = date(year, month, day)
        return parsed.isoformat()
    except ValueError:
        return None


def format_display_date(iso_text: Optional[str]) -> str:
    """Safely extract YYYY-MM-DD date prefix for table display."""
    if not iso_text:
        return ""
    return str(iso_text)[:10]
