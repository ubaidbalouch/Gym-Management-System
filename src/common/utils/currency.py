"""PKR currency formatting and amount validation helpers."""


def format_pkr(amount: float | int | None) -> str:
    """Format a numeric amount as PKR currency."""
    value = float(amount or 0.0)
    return f"PKR {value:,.2f}"


def parse_positive_amount(raw: str, field_name: str = "Amount") -> float:
    """Parse a positive float from user input, raising ValueError with context."""
    cleaned = raw.strip()
    if not cleaned:
        raise ValueError(f"Please enter {field_name}!")
    try:
        value = float(cleaned)
    except ValueError as exc:
        raise ValueError(f"Invalid {field_name}: '{cleaned}'. Please enter a valid number.") from exc
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than 0!")
    return value
