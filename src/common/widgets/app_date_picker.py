"""Themed DD-MM-YYYY date field and calendar spinbox picker dialog."""

from datetime import date
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from src.common.theme import AppTheme
from src.common.utils.dates import parse_ddmmyyyy_to_iso
from .app_button import AppButton
from .app_dialogs import AppModalDialog, show_error
from .app_text_field import AppTextField


class AppDatePickerDialog(AppModalDialog):
    """Modal dialog for picking a valid calendar date as DD-MM-YYYY."""

    def __init__(
        self,
        parent: tk.Misc,
        initial_date_text: str = "",
        on_select: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(parent, title="Select Date", resizable=False)
        self._on_select = on_select

        default = date.today()
        iso = parse_ddmmyyyy_to_iso(initial_date_text)
        if iso:
            default = date.fromisoformat(iso)

        self.day_var = tk.StringVar(value=f"{default.day:02d}")
        self.month_var = tk.StringVar(value=f"{default.month:02d}")
        self.year_var = tk.StringVar(value=str(default.year))

        grid = ttk.Frame(self.body)
        grid.pack(fill="x", pady=(0, AppTheme.spacing.md))

        for row_idx, (label, var, low, high, width) in enumerate(
            (
                ("Day", self.day_var, 1, 31, 6),
                ("Month", self.month_var, 1, 12, 6),
                ("Year", self.year_var, 1900, 2100, 8),
            )
        ):
            ttk.Label(grid, text=label, style="TLabel").grid(
                row=row_idx, column=0, sticky="w", padx=(0, AppTheme.spacing.md), pady=4
            )
            ttk.Spinbox(grid, from_=low, to=high, textvariable=var, width=width).grid(
                row=row_idx, column=1, sticky="ew", pady=4
            )

        actions = ttk.Frame(self.body)
        actions.pack(fill="x")
        AppButton(actions, text="Cancel", variant="secondary", command=self.destroy).pack(
            side="right"
        )
        AppButton(actions, text="Apply", variant="primary", command=self._confirm).pack(
            side="right", padx=(0, AppTheme.spacing.xs)
        )

        self.show_modal()

    def _confirm(self) -> None:
        try:
            picked = date(
                int(self.year_var.get()),
                int(self.month_var.get()),
                int(self.day_var.get()),
            )
        except ValueError:
            show_error("Invalid Date", "Please choose a valid calendar date.", parent=self)
            return

        if self._on_select:
            self._on_select(picked.strftime("%d-%m-%Y"))
        self.destroy()


class AppDateField(AppTextField):
    """Labeled DD-MM-YYYY input field with an integrated date picker button."""

    def __init__(
        self,
        parent,
        label: str = "Date (DD-MM-YYYY)",
        width: int = 18,
        surface: bool = True,
    ) -> None:
        super().__init__(
            parent,
            label=label,
            width=width,
            placeholder="DD-MM-YYYY",
            surface=surface,
            action_text="📅",
            on_action=self._open_picker,
        )

    def _open_picker(self) -> None:
        AppDatePickerDialog(self, initial_date_text=self.get(), on_select=self.set)

    def get_iso(self) -> Optional[str]:
        """Parse current value to YYYY-MM-DD, returning None if blank or invalid."""
        return parse_ddmmyyyy_to_iso(self.get())

    def is_valid_or_empty(self) -> bool:
        """Return True if field is blank or contains a valid DD-MM-YYYY date."""
        raw = self.get().strip()
        if not raw:
            return True
        return parse_ddmmyyyy_to_iso(raw) is not None
