"""Shared Excel export helper with graceful dependency handling."""

from typing import Iterable, Sequence

from src.common.database.db_connection import DatabaseConnection


def export_query_to_excel(
    db: DatabaseConnection,
    query: str,
    filename: str,
    params: Sequence[object] = (),
    fill_na_columns: Iterable[str] = (),
) -> tuple[bool, str]:
    """Execute a SQL query and write results to an Excel file.

    Returns (success, message).
    """
    try:
        import pandas as pd
    except ImportError:
        return (
            False,
            "Excel export requires 'pandas' and 'openpyxl'.\nInstall them with: pip install -r requirements.txt",
        )

    try:
        with db.session() as conn:
            df = pd.read_sql_query(query, conn, params=params)
        for col in fill_na_columns:
            if col in df.columns:
                df[col] = df[col].fillna("N/A")
        df.to_excel(filename, index=False)
        return True, f"Exported successfully to:\n{filename}"
    except Exception as exc:
        return False, f"Failed to export Excel:\n{exc}"
