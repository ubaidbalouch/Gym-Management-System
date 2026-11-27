"""Payment history view listing all member fees and payment dates with status filtering."""

from tkinter import ttk

from src.common.theme import AppTheme
from src.common.utils import format_display_date, format_pkr
from src.common.widgets import (
    AppButton,
    AppCard,
    AppChipGroup,
    AppTable,
    TableColumn,
    status_row_tag,
)
from .payment_repository import PaymentRepository


class PaymentHistoryView(ttk.Frame):
    """Shows full payment history across all members with status filter pills."""

    FILTER_OPTIONS = (
        ("All", "All"),
        ("Paid", "Paid"),
        ("Partial", "Partial"),
        ("Pending", "Pending"),
    )

    def __init__(self, parent, payment_repo: PaymentRepository) -> None:
        super().__init__(parent, padding=AppTheme.spacing.xl)
        self.payment_repo = payment_repo
        self._build_ui()
        self.refresh_history()

    def _build_ui(self) -> None:
        s = AppTheme.spacing

        card = AppCard(
            self,
            title="Ledger History",
            subtitle="Complete breakdown of assigned fees, payments, and dates",
        )
        card.pack(fill="both", expand=True)

        filter_bar = ttk.Frame(card.content, style="Surface.TFrame")
        filter_bar.pack(fill="x", pady=(0, s.md))

        self.filter_chips = AppChipGroup(
            filter_bar,
            options=self.FILTER_OPTIONS,
            initial_key="All",
            on_change=lambda _k: self.refresh_history(),
            surface=True,
        )
        self.filter_chips.pack(side="left")

        AppButton(
            filter_bar, text="Refresh History", variant="outline", pill=True, command=self.refresh_history
        ).pack(side="right")

        self.history_table = AppTable(
            card.content,
            columns=(
                TableColumn("member_name", "Member Name", width=140, anchor="w"),
                TableColumn("member_id", "Member ID", width=80, anchor="center", stretch=False),
                TableColumn("fee_id", "Fee ID", width=65, anchor="center", stretch=False),
                TableColumn("fee_type", "Fee Type", width=130, anchor="w"),
                TableColumn("total", "Total", width=105, anchor="e"),
                TableColumn("paid", "Paid", width=105, anchor="e"),
                TableColumn("pending", "Pending", width=105, anchor="e"),
                TableColumn("status", "Status", width=85, anchor="center"),
                TableColumn("assign_date", "Assign Date", width=95, anchor="center"),
                TableColumn("paid_date", "Paid Date", width=95, anchor="center"),
            ),
            height=17,
            horizontal_scroll=True,
        )
        self.history_table.pack(fill="both", expand=True)

    def refresh_history(self) -> None:
        """Reload payment history matching active status chip."""
        status_filter = self.filter_chips.get_selected()
        fees = self.payment_repo.get_payment_history(status_filter=status_filter)
        rows = [
            (
                f.member_name,
                f.member_id,
                f.fee_id,
                f.fee_name,
                format_pkr(f.total_amount),
                format_pkr(f.paid_amount),
                format_pkr(f.pending_amount),
                f.payment_status,
                format_display_date(f.created_date),
                format_display_date(f.last_payment_date),
            )
            for f in fees
        ]
        self.history_table.set_rows(rows, tag_fn=lambda r, i: status_row_tag(str(r[7]), i))
