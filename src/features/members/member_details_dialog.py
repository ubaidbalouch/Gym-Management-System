"""Modal dialog displaying member profile, assigned fees, and Excel export."""

import tkinter as tk
from tkinter import ttk

from src.common.theme import AppTheme
from src.common.utils import format_display_date, format_pkr
from src.common.widgets import (
    AppButton,
    AppCard,
    AppModalDialog,
    AppTable,
    StatusChip,
    TableColumn,
    ask_save_excel,
    show_error,
    show_info,
    status_row_tag,
)
from src.features.fees.fee_repository import FeeRepository
from src.features.members.member_model import Member


class MemberDetailsDialog(AppModalDialog):
    """Displays a member's details and full fee breakdown."""

    def __init__(self, parent: tk.Misc, member: Member, fee_repo: FeeRepository) -> None:
        super().__init__(parent, title=f"Member Details - {member.name}", width=820, height=540)
        self.member = member
        self.fee_repo = fee_repo
        self._build_ui()
        self._load_fees()
        self.show_modal()

    def _build_ui(self) -> None:
        s = AppTheme.spacing

        profile_card = AppCard(self.body, title=f"{self.member.name} (ID #{self.member.member_id})")
        profile_card.pack(fill="x", pady=(0, s.md))

        info_grid = ttk.Frame(profile_card.content, style="Surface.TFrame")
        info_grid.pack(fill="x")

        items = (
            ("Member ID:", str(self.member.member_id)),
            ("Name:", self.member.name),
            ("Phone:", self.member.phone or "N/A"),
            ("Registered:", format_display_date(self.member.registration_date) or "N/A"),
        )
        for idx, (lbl, val) in enumerate(items):
            r, col = divmod(idx, 2)
            cell = ttk.Frame(info_grid, style="Surface.TFrame")
            cell.grid(row=r, column=col, sticky="w", padx=(0, s.xl), pady=2)
            ttk.Label(cell, text=lbl, style="FieldLabel.TLabel").pack(side="left", padx=(0, s.xs))
            ttk.Label(cell, text=val, style="Surface.TLabel").pack(side="left")

        status_row = ttk.Frame(profile_card.content, style="Surface.TFrame")
        status_row.pack(fill="x", pady=(s.sm, 0))
        ttk.Label(status_row, text="Account Status:", style="FieldLabel.TLabel").pack(
            side="left", padx=(0, s.sm)
        )
        self.overall_chip = StatusChip(status_row, "No Fees")
        self.overall_chip.pack(side="left")

        fees_card = AppCard(self.body, title="Fees & Payment Status")
        fees_card.pack(fill="both", expand=True, pady=(0, s.md))

        self.fees_table = AppTable(
            fees_card.content,
            columns=(
                TableColumn("fee_id", "Fee ID", width=65, anchor="center", stretch=False),
                TableColumn("type", "Type", width=130, anchor="w"),
                TableColumn("total", "Total", width=100, anchor="e"),
                TableColumn("paid", "Paid", width=100, anchor="e"),
                TableColumn("pending", "Pending", width=100, anchor="e"),
                TableColumn("status", "Status", width=85, anchor="center"),
                TableColumn("method", "Method", width=100, anchor="center"),
                TableColumn("date", "Assign Date", width=95, anchor="center"),
            ),
            height=11,
        )
        self.fees_table.pack(fill="both", expand=True)

        actions = ttk.Frame(self.body)
        actions.pack(fill="x")
        AppButton(actions, text="Close", variant="secondary", command=self.destroy).pack(
            side="right"
        )
        AppButton(actions, text="Download Excel", variant="primary", command=self._export_excel).pack(
            side="right", padx=(0, s.sm)
        )

    def _load_fees(self) -> None:
        fees = self.fee_repo.get_member_fees(self.member.member_id)
        if not fees:
            self.overall_chip.set_status("No Fees")
            self.fees_table.set_rows([("—", "No fees assigned", "", "", "", "", "", "")])
            return

        total = sum(f.total_amount for f in fees)
        paid = sum(f.paid_amount for f in fees)
        overall = "Paid" if (total - paid) <= 0 else ("Partial" if paid > 0 else "Pending")
        self.overall_chip.set_status(overall)

        rows = [
            (
                f.fee_id,
                f.fee_name,
                format_pkr(f.total_amount),
                format_pkr(f.paid_amount),
                format_pkr(f.pending_amount),
                f.payment_status,
                f.last_payment_method,
                format_display_date(f.created_date),
            )
            for f in fees
        ]
        self.fees_table.set_rows(rows, tag_fn=lambda r, i: status_row_tag(str(r[5]), i))

    def _export_excel(self) -> None:
        filename = ask_save_excel(
            initial_filename=f"member_{self.member.member_id}_details.xlsx",
            parent=self,
        )
        if not filename:
            return
        ok, msg = self.fee_repo.export_member_fees_excel(self.member.member_id, filename)
        if ok:
            show_info("Export Complete", msg, parent=self)
        else:
            show_error("Export Failed", msg, parent=self)
