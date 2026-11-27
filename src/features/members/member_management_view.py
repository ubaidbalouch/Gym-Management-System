"""Member management view using shadcn/ui AppTheme and common widgets."""

from tkinter import ttk
from typing import Callable, Optional

from src.common.theme import AppTheme
from src.common.utils import format_display_date
from src.common.widgets import (
    AppButton,
    AppCard,
    AppTable,
    AppTextField,
    TableColumn,
    ask_confirm,
    show_error,
    show_info,
    show_warning,
)
from src.features.fees.fee_repository import FeeRepository
from .member_details_dialog import MemberDetailsDialog
from .member_repository import MemberRepository


class MemberManagementView(ttk.Frame):
    """CRUD interface for registering, editing, inspecting, and deleting gym members."""

    def __init__(
        self,
        parent,
        member_repo: MemberRepository,
        fee_repo: FeeRepository,
        on_data_changed: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent, padding=AppTheme.spacing.xl)
        self.member_repo = member_repo
        self.fee_repo = fee_repo
        self.on_data_changed = on_data_changed
        self._build_ui()
        self.refresh_members_list()

    def _build_ui(self) -> None:
        s = AppTheme.spacing

        form_card = AppCard(
            self,
            title="Add / Edit Member",
            subtitle="Register a new member or choose an existing row below to edit details",
        )
        form_card.pack(fill="x", pady=(0, s.md))

        fields_row = ttk.Frame(form_card.content, style="Surface.TFrame")
        fields_row.pack(fill="x", pady=(0, s.md))

        self.member_id_field = AppTextField(
            fields_row, label="Member ID", width=12, readonly=True
        )
        self.member_id_field.grid(row=0, column=0, sticky="ew", padx=(0, s.md))

        self.name_field = AppTextField(
            fields_row,
            label="Full Name *",
            width=30,
            placeholder="e.g. Ali Raza",
            on_submit=self._submit_form,
        )
        self.name_field.grid(row=0, column=1, sticky="ew", padx=(0, s.md))

        self.phone_field = AppTextField(
            fields_row,
            label="Phone Number",
            width=24,
            placeholder="e.g. 0300-1234567",
            on_submit=self._submit_form,
        )
        self.phone_field.grid(row=0, column=2, sticky="ew")

        fields_row.columnconfigure(0, weight=1)
        fields_row.columnconfigure(1, weight=2)
        fields_row.columnconfigure(2, weight=2)

        btn_row = ttk.Frame(form_card.content, style="Surface.TFrame")
        btn_row.pack(fill="x")
        AppButton(btn_row, text="Add Member", variant="primary", pill=True, command=self.add_member).pack(
            side="left", padx=(0, s.sm)
        )
        AppButton(btn_row, text="Update Member", variant="outline", pill=True, command=self.update_member).pack(
            side="left", padx=(0, s.sm)
        )
        AppButton(btn_row, text="Reset Form", variant="ghost", pill=True, command=self.reset_form_fields).pack(
            side="left"
        )
        AppButton(btn_row, text="Clear All Data", variant="danger", pill=True, command=self.clear_all_data).pack(
            side="right"
        )

        list_card = AppCard(
            self,
            title="Members Directory",
            subtitle="Double-click a member row to inspect assigned fees and download their report",
        )
        list_card.pack(fill="both", expand=True)

        self.members_table = AppTable(
            list_card.content,
            columns=(
                TableColumn("id", "Member ID", width=95, anchor="center", stretch=False),
                TableColumn("name", "Name", width=260, anchor="w"),
                TableColumn("phone", "Phone", width=180, anchor="w"),
                TableColumn("registered", "Registration Date", width=140, anchor="center"),
            ),
            height=12,
            on_double_click=lambda _v: self.open_selected_details(),
        )
        self.members_table.pack(fill="both", expand=True, pady=(0, s.md))

        actions_row = ttk.Frame(list_card.content, style="Surface.TFrame")
        actions_row.pack(fill="x")
        AppButton(
            actions_row, text="View Details", variant="primary", pill=True, command=self.open_selected_details
        ).pack(side="left", padx=(0, s.sm))
        AppButton(
            actions_row, text="Edit Selected", variant="outline", pill=True, command=self.edit_selected
        ).pack(side="left", padx=(0, s.sm))
        AppButton(
            actions_row, text="Delete Selected", variant="danger", pill=True, command=self.delete_selected
        ).pack(side="left")

    def _submit_form(self) -> None:
        if self.member_id_field.get().strip():
            self.update_member()
        else:
            self.add_member()

    def _notify_changed(self) -> None:
        if self.on_data_changed:
            self.on_data_changed()

    def reset_form_fields(self) -> None:
        """Clear input fields and table selection without touching database records."""
        self.member_id_field.clear()
        self.name_field.clear()
        self.phone_field.clear()
        self.members_table.clear_selection()
        self.name_field.focus()

    def refresh_members_list(self) -> None:
        """Reload all members from repository into the table."""
        members = self.member_repo.get_all()
        rows = [
            (m.member_id, m.name, m.phone, format_display_date(m.registration_date))
            for m in members
        ]
        self.members_table.set_rows(rows)

    def add_member(self) -> None:
        """Validate inputs and create a new member."""
        name = self.name_field.get().strip()
        if not name:
            self.name_field.set_error("Name is required.")
            self.name_field.focus()
            return

        phone = self.phone_field.get().strip()
        self.member_repo.create(name, phone)
        self.reset_form_fields()
        self.refresh_members_list()
        self._notify_changed()

    def edit_selected(self) -> None:
        """Populate form fields with the selected member while keeping Member ID readonly."""
        selected = self.members_table.get_selected_values()
        if not selected:
            show_warning("Selection Required", "Please select a member to edit!", parent=self)
            return

        self.member_id_field.set(selected[0])
        self.name_field.set(selected[1])
        self.phone_field.set(selected[2])
        self.name_field.focus()

    def update_member(self) -> None:
        """Update the selected member in the database."""
        raw_id = self.member_id_field.get().strip()
        if not raw_id:
            show_warning("Selection Required", "Please select a member to update!", parent=self)
            return
        name = self.name_field.get().strip()
        if not name:
            self.name_field.set_error("Name is required.")
            self.name_field.focus()
            return

        try:
            member_id = int(raw_id)
        except ValueError:
            show_error("Error", "Invalid Member ID!", parent=self)
            return

        if self.member_repo.update(member_id, name, self.phone_field.get().strip()):
            self.reset_form_fields()
            self.refresh_members_list()
            self._notify_changed()
        else:
            show_error("Error", "Failed to update member!", parent=self)

    def delete_selected(self) -> None:
        """Delete the selected member and all associated fees/payments."""
        selected = self.members_table.get_selected_values()
        if not selected:
            show_warning("Selection Required", "Please select a member to delete!", parent=self)
            return

        member_id = int(selected[0])
        member_name = str(selected[1])
        if not ask_confirm(
            "Confirm Delete",
            f"Delete {member_name} (#{member_id}) and all associated fees & payments?",
            icon="warning",
            parent=self,
        ):
            return

        if self.member_repo.delete(member_id):
            self.reset_form_fields()
            self.refresh_members_list()
            self._notify_changed()
        else:
            show_error("Error", "Failed to delete member!", parent=self)

    def clear_all_data(self) -> None:
        """Permanently wipe all members, fees, and payments after double confirmation."""
        members = self.member_repo.get_all()
        if not members:
            show_info("Info", "No members to delete. Database is already empty.", parent=self)
            return

        count = len(members)
        if not ask_confirm(
            "Confirm Delete All",
            f"This will delete ALL {count} member(s), fees, and payment records.\n"
            "This action CANNOT be undone.\n\nContinue?",
            icon="warning",
            parent=self,
        ):
            return

        if not ask_confirm(
            "Final Confirmation",
            "LAST WARNING: Permanently delete all members, fees, and payments?",
            icon="error",
            parent=self,
        ):
            return

        self.member_repo.delete_all()
        self.reset_form_fields()
        self.refresh_members_list()
        self._notify_changed()
        show_info("Success", f"All data cleared ({count} member(s) removed).", parent=self)

    def open_selected_details(self) -> None:
        """Open the MemberDetailsDialog for the currently selected table row."""
        selected = self.members_table.get_selected_values()
        if not selected:
            show_warning("Selection Required", "Please select a member!", parent=self)
            return

        member = self.member_repo.get_by_id(int(selected[0]))
        if not member:
            show_error("Not Found", f"Member ID {selected[0]} not found.", parent=self)
            return

        MemberDetailsDialog(self, member, self.fee_repo)
