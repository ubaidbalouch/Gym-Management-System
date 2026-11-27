"""Payment management view (assign fees, record payments, and select Fee ID dialog)."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from src.common.theme import AppTheme
from src.common.utils import format_pkr, parse_positive_amount
from src.common.widgets import (
    AppButton,
    AppCard,
    AppDateField,
    AppDropdown,
    AppModalDialog,
    AppTable,
    AppTextField,
    TableColumn,
    show_error,
    show_info,
    status_row_tag,
)
from src.features.fees.fee_repository import FeeRepository
from src.features.members.member_repository import MemberRepository
from .payment_repository import PaymentRepository


class FeeSelectorDialog(AppModalDialog):
    """Modal picker listing assigned fees for quick Fee ID selection."""

    def __init__(
        self,
        parent: tk.Misc,
        fee_repo: FeeRepository,
        on_select_fee: Callable[[int], None],
    ) -> None:
        super().__init__(parent, title="Available Fees - Select Fee ID", width=780, height=440)
        self._on_select_fee = on_select_fee

        ttk.Label(
            self.body,
            text="Double-click a fee row (or select and click Choose) to populate Fee ID",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(0, AppTheme.spacing.sm))

        self.table = AppTable(
            self.body,
            columns=(
                TableColumn("fee_id", "Fee ID", width=70, anchor="center", stretch=False),
                TableColumn("member", "Member", width=150, anchor="w"),
                TableColumn("fee_type", "Fee Type", width=140, anchor="w"),
                TableColumn("total", "Total", width=105, anchor="e"),
                TableColumn("paid", "Paid", width=105, anchor="e"),
                TableColumn("pending", "Pending", width=105, anchor="e"),
                TableColumn("status", "Status", width=85, anchor="center"),
            ),
            height=11,
            on_double_click=lambda v: self._choose(int(v[0])),
        )
        self.table.pack(fill="both", expand=True, pady=(0, AppTheme.spacing.md))

        fees = fee_repo.get_all_fees()
        rows = [
            (
                f.fee_id,
                f.member_name,
                f.fee_name,
                format_pkr(f.total_amount),
                format_pkr(f.paid_amount),
                format_pkr(f.pending_amount),
                f.payment_status,
            )
            for f in fees
        ]
        self.table.set_rows(rows, tag_fn=lambda r, i: status_row_tag(str(r[6]), i))

        actions = ttk.Frame(self.body)
        actions.pack(fill="x")
        AppButton(actions, text="Cancel", variant="outline", command=self.destroy).pack(
            side="right"
        )
        AppButton(
            actions, text="Choose Selected", variant="primary", command=self._choose_selected
        ).pack(side="right", padx=(0, AppTheme.spacing.sm))

        self.show_modal()

    def _choose_selected(self) -> None:
        selected = self.table.get_selected_values()
        if selected:
            self._choose(int(selected[0]))

    def _choose(self, fee_id: int) -> None:
        self._on_select_fee(fee_id)
        self.destroy()


class PaymentManagementView(ttk.Frame):
    """Side-by-side cards for assigning fees to members and recording PKR payments."""

    def __init__(
        self,
        parent,
        member_repo: MemberRepository,
        fee_repo: FeeRepository,
        payment_repo: PaymentRepository,
        on_data_changed: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent, padding=AppTheme.spacing.xl)
        self.member_repo = member_repo
        self.fee_repo = fee_repo
        self.payment_repo = payment_repo
        self.on_data_changed = on_data_changed
        self._build_ui()
        self.populate_dropdowns()

    def _build_ui(self) -> None:
        s = AppTheme.spacing

        cards_grid = ttk.Frame(self)
        cards_grid.pack(fill="both", expand=True)

        # Left Card: Assign Fee
        assign_card = AppCard(
            cards_grid,
            title="Assign Fee to Member",
            subtitle="Create a new fee obligation for any registered member",
        )
        assign_card.grid(row=0, column=0, sticky="nsew", padx=(0, s.md))

        self.member_dropdown = AppDropdown(
            assign_card.content,
            label="Member *",
            postcommand=self.populate_members_dropdown,
        )
        self.member_dropdown.pack(fill="x", pady=(0, s.md))

        self.fee_type_dropdown = AppDropdown(assign_card.content, label="Fee Type *")
        self.fee_type_dropdown.pack(fill="x", pady=(0, s.md))

        self.assign_amount_field = AppTextField(
            assign_card.content, label="Amount (PKR) *", placeholder="e.g. 3000"
        )
        self.assign_amount_field.pack(fill="x", pady=(0, s.md))

        self.assigned_date_field = AppDateField(
            assign_card.content, label="Assigned Date (DD-MM-YYYY)"
        )
        self.assigned_date_field.pack(fill="x", pady=(0, s.md))

        self.assign_notes_field = AppTextField(
            assign_card.content, label="Notes", placeholder="Optional fee notes"
        )
        self.assign_notes_field.pack(fill="x", pady=(0, s.lg))

        AppButton(
            assign_card.content, text="Assign Fee", variant="primary", command=self.assign_fee
        ).pack(anchor="w")

        # Right Card: Record Payment
        payment_card = AppCard(
            cards_grid,
            title="Record Payment",
            subtitle="Apply a partial or full PKR payment to an existing fee",
        )
        payment_card.grid(row=0, column=1, sticky="nsew")

        self.payment_fee_id_field = AppTextField(
            payment_card.content,
            label="Fee ID *",
            placeholder="Enter or pick Fee ID",
            action_text="Pick",
            on_action=self.show_fees_list,
        )
        self.payment_fee_id_field.pack(fill="x", pady=(0, s.md))

        self.payment_amount_field = AppTextField(
            payment_card.content, label="Payment Amount (PKR) *", placeholder="e.g. 1500"
        )
        self.payment_amount_field.pack(fill="x", pady=(0, s.md))

        self.payment_method_dropdown = AppDropdown(
            payment_card.content,
            label="Payment Method",
            options=PaymentRepository.PAYMENT_METHODS,
            initial_value="Cash",
            readonly=False,
        )
        self.payment_method_dropdown.pack(fill="x", pady=(0, s.md))

        self.payment_date_field = AppDateField(
            payment_card.content, label="Payment Date (DD-MM-YYYY)"
        )
        self.payment_date_field.pack(fill="x", pady=(0, s.md))

        self.payment_notes_field = AppTextField(
            payment_card.content, label="Notes", placeholder="Optional receipt / note"
        )
        self.payment_notes_field.pack(fill="x", pady=(0, s.lg))

        AppButton(
            payment_card.content,
            text="Record Payment",
            variant="primary",
            command=self.record_payment,
        ).pack(anchor="w")

        cards_grid.columnconfigure(0, weight=1, uniform="paycols")
        cards_grid.columnconfigure(1, weight=1, uniform="paycols")
        cards_grid.rowconfigure(0, weight=1)

    def populate_dropdowns(self) -> None:
        """Refresh member and fee-type dropdown options."""
        self.populate_members_dropdown()
        fee_types = self.fee_repo.get_fee_types()
        self.fee_type_dropdown.set_options(
            [f"{ft.fee_type_id} - {ft.fee_name}" for ft in fee_types]
        )

    def populate_members_dropdown(self) -> None:
        """Refresh the registered members dropdown."""
        members = self.member_repo.get_all()
        self.member_dropdown.set_options([f"{m.member_id} - {m.name}" for m in members])

    def show_fees_list(self) -> None:
        """Open the FeeSelectorDialog if fees exist."""
        fees = self.fee_repo.get_all_fees()
        if not fees:
            show_info("Info", "No fees found. Please assign fees to members first.", parent=self)
            return
        FeeSelectorDialog(self, self.fee_repo, lambda fid: self.payment_fee_id_field.set(fid))

    def _notify_changed(self) -> None:
        if self.on_data_changed:
            self.on_data_changed()

    def assign_fee(self) -> None:
        """Validate inputs and assign a new fee to the chosen member."""
        member_val = self.member_dropdown.get().strip()
        fee_type_val = self.fee_type_dropdown.get().strip()
        has_error = False
        if not member_val:
            self.member_dropdown.set_error("Please select a member.")
            has_error = True
        if not fee_type_val:
            self.fee_type_dropdown.set_error("Please select a fee type.")
            has_error = True
        if not self.assigned_date_field.is_valid_or_empty():
            self.assigned_date_field.set_error("Use DD-MM-YYYY format.")
            has_error = True
        if has_error:
            return

        try:
            amount = parse_positive_amount(self.assign_amount_field.get(), "Amount")
        except ValueError as exc:
            self.assign_amount_field.set_error(str(exc))
            self.assign_amount_field.focus()
            return

        try:
            member_id = int(member_val.split(" - ")[0])
            fee_type_id = int(fee_type_val.split(" - ")[0])
            fee_id = self.fee_repo.assign_fee(
                member_id=member_id,
                fee_type_id=fee_type_id,
                amount=amount,
                assigned_date=self.assigned_date_field.get_iso(),
                notes=self.assign_notes_field.get(),
            )
        except ValueError as exc:
            self.assign_amount_field.set_error(str(exc))
            return
        except Exception as exc:
            show_error("Error", f"Failed to assign fee:\n{exc}", parent=self)
            return

        self.assign_amount_field.clear()
        self.assigned_date_field.clear()
        self.assign_notes_field.clear()
        self._notify_changed()
        show_info(
            "Success",
            f"Fee assigned successfully!\nFee ID: {fee_id}\nAmount: {format_pkr(amount)}",
            parent=self,
        )

    def record_payment(self) -> None:
        """Validate inputs and record a payment transaction against a fee."""
        raw_fee_id = self.payment_fee_id_field.get().strip()
        if not raw_fee_id:
            self.payment_fee_id_field.set_error("Fee ID is required.")
            self.payment_fee_id_field.focus()
            return
        try:
            fee_id = int(raw_fee_id)
        except ValueError:
            self.payment_fee_id_field.set_error("Must be a numeric Fee ID.")
            self.payment_fee_id_field.focus()
            return

        if not self.payment_date_field.is_valid_or_empty():
            self.payment_date_field.set_error("Use DD-MM-YYYY format.")
            self.payment_date_field.focus()
            return

        try:
            amount = parse_positive_amount(self.payment_amount_field.get(), "Payment Amount")
        except ValueError as exc:
            self.payment_amount_field.set_error(str(exc))
            self.payment_amount_field.focus()
            return

        try:
            new_status = self.payment_repo.record_payment(
                fee_id=fee_id,
                amount=amount,
                payment_method=self.payment_method_dropdown.get() or "Cash",
                notes=self.payment_notes_field.get(),
                payment_date=self.payment_date_field.get_iso(),
            )
        except ValueError as exc:
            self.payment_fee_id_field.set_error(str(exc))
            return
        except Exception as exc:
            show_error("Database Error", f"Failed to record payment:\n{exc}", parent=self)
            return

        self.payment_fee_id_field.clear()
        self.payment_amount_field.clear()
        self.payment_date_field.clear()
        self.payment_notes_field.clear()
        self._notify_changed()
        show_info(
            "Success",
            f"Payment of {format_pkr(amount)} recorded!\nFee ID: {fee_id}\nNew Status: {new_status}",
            parent=self,
        )
