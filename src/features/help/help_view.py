"""Help & user guide view styled as a clean 2x2 shadcn/ui card grid."""

from tkinter import ttk

from src.common.theme import AppTheme
from src.common.widgets import AppCard

_HELP_CARDS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "Dashboard & KPIs",
        "Monitor member totals, receivables, and status counts",
        (
            "Track total registered members and open pending/partial fee counts",
            "Review gross billed, collected, and remaining PKR balances",
            "Export the complete payment breakdown report directly to Excel (.xlsx)",
        ),
    ),
    (
        "Member Management",
        "Register members and inspect account ledgers",
        (
            "Add new members with Name and Phone; Member IDs generate automatically",
            "Select a directory row and click Edit Selected to update profile details",
            "Double-click any row to open the full Member Details & export dialog",
        ),
    ),
    (
        "Fees & Payments (PKR)",
        "Assign fee categories and apply partial or full payments",
        (
            "Assign Monthly, Admission, Personal Training, or Supplement fees",
            "Use the Pick action in Record Payment to browse and select a Fee ID",
            "Record partial or full payments via Cash, Card, Bank Transfer, Jazz Cash, or Easy Paisa",
        ),
    ),
    (
        "Search, History & Storage",
        "Filter ledgers, search accounts, and keep data safe",
        (
            "Use pill filters in Member Fees and Payment History to isolate Paid, Partial, or Pending records",
            "Search instantly by Member ID, name, or phone in Search & Reports",
            "All updates commit transactionally to the local SQLite database (gym.db)",
        ),
    ),
)


class HelpView(ttk.Frame):
    """Displays structured usage cards for the Gym Management System."""

    def __init__(self, parent) -> None:
        super().__init__(parent, padding=AppTheme.spacing.xl)
        self._build_ui()

    def _build_ui(self) -> None:
        s = AppTheme.spacing

        grid = ttk.Frame(self)
        grid.pack(fill="both", expand=True)

        for idx, (title, subtitle, bullets) in enumerate(_HELP_CARDS):
            row, col = divmod(idx, 2)
            card = AppCard(grid, title=title, subtitle=subtitle)
            card.grid(
                row=row,
                column=col,
                sticky="nsew",
                padx=(0, s.md if col == 0 else 0),
                pady=(0, s.md if row == 0 else 0),
            )
            for bullet in bullets:
                ttk.Label(
                    card.content,
                    text=f"•  {bullet}",
                    style="Surface.TLabel",
                    wraplength=420,
                    justify="left",
                ).pack(anchor="w", pady=(0, s.sm))

        grid.columnconfigure(0, weight=1, uniform="helpcols")
        grid.columnconfigure(1, weight=1, uniform="helpcols")
        grid.rowconfigure(0, weight=1)
        grid.rowconfigure(1, weight=1)
