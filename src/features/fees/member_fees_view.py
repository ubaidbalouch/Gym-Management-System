"""Member Fees view with segmented status filter pills, data table, and Excel export."""

from tkinter import ttk

from src.common.theme import AppTheme
from src.common.utils import format_display_date, format_pkr
from src.common.widgets import (
    AppButton,
    AppCard,
    AppChipGroup,
    AppTable,
    TableColumn,
    ask_save_excel,
    show_error,
    show_info,
    status_row_tag,
)
from .fee_repository import FeeRepository


class MemberFeesView(ttk.Frame):
    """Displays all assigned member fees with status chip filtering and Excel export."""

    FILTER_OPTIONS = (
        ("All", "All"),
        ("Paid", "Paid"),
        ("Partial", "Partial"),
        ("Pending", "Pending"),
    )

    def __init__(self, parent, fee_repo: FeeRepository) -> None:
        super().__init__(parent, padding=AppTheme.spacing.xl)
        self.fee_repo = fee_repo
        self._build_ui()
        self.refresh_fees_list()

    def _build_ui(self) -> None:
        s = AppTheme.spacing

        card = AppCard(
            self,
            title="All Assigned Fees",
            subtitle="Filter fee records by payment status or export the full ledger",
        )
        card.pack(fill="both", expand=True)

        filter_bar = ttk.Frame(card.content, style="Surface.TFrame")
        filter_bar.pack(fill="x", pady=(0, s.md))

        self.filter_chips = AppChipGroup(
            filter_bar,
            options=self.FILTER_OPTIONS,
            initial_key="All",
            on_change=lambda _key: self.refresh_fees_list(),
            surface=True,
        )
        self.filter_chips.pack(side="left")

        AppButton(
            filter_bar, text="Export to Excel", variant="primary", pill=True, command=self.export_fees
        ).pack(side="right")
        AppButton(
            filter_bar, text="Refresh", variant="outline", pill=True, command=self.refresh_fees_list
        ).pack(side="right", padx=(0, s.sm))

        self.fees_table = AppTable(
            card.content,
            columns=(
                TableColumn("fee_id", "Fee ID", width=65, anchor="center", stretch=False),
                TableColumn("member", "Member", width=140, anchor="w"),
                TableColumn("fee_type", "Fee Type", width=130, anchor="w"),
                TableColumn("total", "Total", width=105, anchor="e"),
                TableColumn("paid", "Paid", width=105, anchor="e"),
                TableColumn("pending", "Pending", width=105, anchor="e"),
                TableColumn("status", "Status", width=85, anchor="center"),
                TableColumn("method", "Method", width=105, anchor="center"),
                TableColumn("assign_date", "Assign Date", width=95, anchor="center"),
                TableColumn("paid_date", "Paid Date", width=95, anchor="center"),
                TableColumn("notes", "Notes", width=150, anchor="w"),
            ),
            height=17,
            horizontal_scroll=True,
        )
        self.fees_table.pack(fill="both", expand=True)

    def refresh_fees_list(self) -> None:
        """Reload member fees matching the active filter chip."""
        status_filter = self.filter_chips.get_selected()
        fees = self.fee_repo.get_all_fees(status_filter=status_filter)
        rows = [
            (
                f.fee_id,
                f.member_name,
                f.fee_name,
                format_pkr(f.total_amount),
                format_pkr(f.paid_amount),
                format_pkr(f.pending_amount),
                f.payment_status,
                f.last_payment_method,
                format_display_date(f.created_date),
                format_display_date(f.last_payment_date),
                f.notes,
            )
            for f in fees
        ]
        self.fees_table.set_rows(rows, tag_fn=lambda r, i: status_row_tag(str(r[6]), i))

    def export_fees(self) -> None:
        """Export all fees to an Excel workbook."""
        filename = ask_save_excel(initial_filename="member_fees.xlsx", parent=self)
        if not filename:
            return
        ok, msg = self.fee_repo.export_all_fees_excel(filename)
        if ok:
            show_info("Export Complete", msg, parent=self)
        else:
            show_error("Export Failed", msg, parent=self)
