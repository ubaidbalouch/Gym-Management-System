"""Search & Reports view for querying members and inspecting their fee history."""

from tkinter import ttk
from typing import Optional

from src.common.theme import AppTheme
from src.common.utils import format_display_date, format_pkr
from src.common.widgets import (
    AppButton,
    AppCard,
    AppTable,
    AppTextField,
    StatusChip,
    TableColumn,
    ask_save_excel,
    show_error,
    show_info,
    show_warning,
    status_row_tag,
)
from src.features.fees.fee_repository import FeeRepository
from .search_repository import SearchRepository


class SearchView(ttk.Frame):
    """Search members by ID, name, or phone and inspect/export their fee history."""

    def __init__(self, parent, search_repo: SearchRepository, fee_repo: FeeRepository) -> None:
        super().__init__(parent, padding=AppTheme.spacing.xl)
        self.search_repo = search_repo
        self.fee_repo = fee_repo
        self._selected_member_id: Optional[int] = None
        self._build_ui()
        self.search_members()

    def _build_ui(self) -> None:
        s = AppTheme.spacing

        search_card = AppCard(self, title="Find Member")
        search_card.pack(fill="x", pady=(0, s.md))

        bar = ttk.Frame(search_card.content, style="Surface.TFrame")
        bar.pack(fill="x")

        self.search_field = AppTextField(
            bar,
            width=40,
            placeholder="Search by Member ID, name, or phone...",
            on_submit=self.search_members,
        )
        self.search_field.pack(side="left", fill="x", expand=True, padx=(0, s.sm))
        AppButton(bar, text="Search", variant="primary", pill=True, command=self.search_members).pack(
            side="left", padx=(0, s.xs)
        )
        AppButton(bar, text="Clear", variant="outline", pill=True, command=self.clear_search).pack(
            side="left"
        )

        results_card = AppCard(
            self,
            title="Matching Members",
            subtitle="Select or double-click a member to load their full fee history below",
        )
        results_card.pack(fill="both", expand=True, pady=(0, s.md))

        self.results_table = AppTable(
            results_card.content,
            columns=(
                TableColumn("id", "ID", width=65, anchor="center", stretch=False),
                TableColumn("name", "Name", width=180, anchor="w"),
                TableColumn("phone", "Phone", width=130, anchor="w"),
                TableColumn("status", "Payment Status", width=110, anchor="center"),
                TableColumn("total", "Total Fees", width=115, anchor="e"),
                TableColumn("paid", "Paid Amount", width=115, anchor="e"),
                TableColumn("pending", "Pending Amount", width=115, anchor="e"),
            ),
            height=6,
            on_select=self._on_member_row_selected,
            on_double_click=self._on_member_row_selected,
        )
        self.results_table.pack(fill="both", expand=True)

        history_card = AppCard(self, title="Selected Member Fee History")
        history_card.pack(fill="both", expand=True)

        meta_bar = ttk.Frame(history_card.content, style="Surface.TFrame")
        meta_bar.pack(fill="x", pady=(0, s.sm))

        self.selected_name_field = AppTextField(
            meta_bar, label="", width=28, readonly=True, initial_value="No member selected"
        )
        self.selected_name_field.pack(side="left", padx=(0, s.sm))

        self.selected_status_chip = StatusChip(meta_bar, "No Fees")
        self.selected_status_chip.pack(side="left")

        AppButton(
            meta_bar,
            text="Export Member Report",
            variant="primary",
            pill=True,
            command=self.export_member_report,
        ).pack(side="right")

        self.history_table = AppTable(
            history_card.content,
            columns=(
                TableColumn("fee_id", "Fee ID", width=65, anchor="center", stretch=False),
                TableColumn("type", "Type", width=150, anchor="w"),
                TableColumn("total", "Total", width=110, anchor="e"),
                TableColumn("paid", "Paid", width=110, anchor="e"),
                TableColumn("pending", "Pending", width=110, anchor="e"),
                TableColumn("status", "Status", width=90, anchor="center"),
                TableColumn("date", "Assign Date", width=105, anchor="center"),
            ),
            height=5,
        )
        self.history_table.pack(fill="both", expand=True)

    def search_members(self) -> None:
        """Query members matching the search term and display financial summaries."""
        term = self.search_field.get()
        members = self.search_repo.search_members(term)
        rows = []
        for member in members:
            details = self.search_repo.get_member_comprehensive_details(member.member_id)
            if not details:
                continue
            rows.append(
                (
                    member.member_id,
                    member.name,
                    member.phone,
                    details.overall_status,
                    format_pkr(details.total_fees),
                    format_pkr(details.paid_amount),
                    format_pkr(details.pending_amount),
                )
            )
        self.results_table.set_rows(rows, tag_fn=lambda r, i: status_row_tag(str(r[3]), i))

    def clear_search(self) -> None:
        """Clear search query and reset results and history panels."""
        self.search_field.clear()
        self._selected_member_id = None
        self.selected_name_field.set("No member selected")
        self.selected_status_chip.set_status("No Fees")
        self.history_table.clear()
        self.search_members()

    def _on_member_row_selected(self, values: tuple) -> None:
        member_id = int(values[0])
        details = self.search_repo.get_member_comprehensive_details(member_id)
        if not details:
            return
        self._selected_member_id = member_id
        self.selected_name_field.set(f"{details.member.name} (ID #{member_id})")
        self.selected_status_chip.set_status(details.overall_status)

        history_rows = [
            (
                f.fee_id,
                f.fee_name,
                format_pkr(f.total_amount),
                format_pkr(f.paid_amount),
                format_pkr(f.pending_amount),
                f.payment_status,
                format_display_date(f.created_date),
            )
            for f in details.fees
        ]
        self.history_table.set_rows(history_rows, tag_fn=lambda r, i: status_row_tag(str(r[5]), i))

    def export_member_report(self) -> None:
        """Export the selected member's fee details to Excel."""
        if self._selected_member_id is None:
            show_warning("Selection Required", "Please select a member first!", parent=self)
            return
        filename = ask_save_excel(
            initial_filename=f"member_{self._selected_member_id}_report.xlsx",
            parent=self,
        )
        if not filename:
            return
        ok, msg = self.fee_repo.export_member_fees_excel(self._selected_member_id, filename)
        if ok:
            show_info("Export Complete", msg, parent=self)
        else:
            show_error("Export Failed", msg, parent=self)
