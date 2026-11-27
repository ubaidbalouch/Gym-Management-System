"""Dashboard summary view with shadcn/ui KPI cards, status pills, and breakdown table."""

from tkinter import ttk
from typing import Optional

from src.common.theme import AppTheme
from src.common.utils import format_pkr
from src.common.widgets import (
    AppButton,
    AppCard,
    AppTable,
    StatCard,
    StatusChip,
    TableColumn,
    ask_save_excel,
    show_error,
    show_info,
    status_row_tag,
)
from .dashboard_repository import DashboardRepository


class DashboardView(ttk.Frame):
    """Displays gym financial KPIs, payment status breakdown, and report export."""

    AUTO_REFRESH_MS = 5000

    def __init__(self, parent, repository: DashboardRepository) -> None:
        super().__init__(parent, padding=AppTheme.spacing.xl)
        self.repository = repository
        self._after_id: Optional[str] = None
        self._build_ui()
        self.refresh_stats()
        self._schedule_refresh()
        self.bind("<Destroy>", self._on_destroy, add="+")

    def _build_ui(self) -> None:
        s = AppTheme.spacing
        c = AppTheme.colors

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, s.md))
        ttk.Label(toolbar, text="Overview", style="Title.TLabel").pack(side="left")
        AppButton(
            toolbar,
            text="Export Payment Report",
            variant="primary",
            pill=True,
            command=self.export_payments,
        ).pack(side="right")
        AppButton(
            toolbar,
            text="Refresh",
            variant="outline",
            pill=True,
            command=self.refresh_stats,
        ).pack(side="right", padx=(0, s.sm))

        # KPI Cards Grid (Row 0 & Row 1)
        stats_grid = ttk.Frame(self)
        stats_grid.pack(fill="x", pady=(0, s.md))

        self.total_members_card = StatCard(
            stats_grid,
            "Total Members",
            "0",
            caption="Registered accounts",
            badge_text="Members",
        )
        self.total_members_card.grid(row=0, column=0, sticky="nsew", padx=(0, s.md), pady=(0, s.md))

        self.pending_count_card = StatCard(
            stats_grid,
            "Pending / Partial Fees",
            "0",
            caption="Unsettled fee records",
            badge_text="Open",
            dot_color=c.warning,
        )
        self.pending_count_card.grid(row=0, column=1, sticky="nsew", padx=(0, s.md), pady=(0, s.md))

        self.total_fees_card = StatCard(
            stats_grid,
            "Total Fees Assigned",
            format_pkr(0),
            caption="Gross billed amount",
            badge_text="PKR",
        )
        self.total_fees_card.grid(row=0, column=2, sticky="nsew", pady=(0, s.md))

        self.total_paid_card = StatCard(
            stats_grid,
            "Total Collected",
            format_pkr(0),
            caption="Received payments",
            badge_text="Paid",
            dot_color=c.success,
        )
        self.total_paid_card.grid(row=1, column=0, sticky="nsew", padx=(0, s.md))

        self.total_pending_card = StatCard(
            stats_grid,
            "Total Outstanding",
            format_pkr(0),
            caption="Remaining balance",
            badge_text="Due",
            dot_color=c.danger,
        )
        self.total_pending_card.grid(row=1, column=1, sticky="nsew", padx=(0, s.md))

        quick_card = AppCard(stats_grid, padding=s.lg)
        quick_card.grid(row=1, column=2, sticky="nsew")
        ttk.Label(
            quick_card.content,
            text="Status Summary",
            style="SurfaceMuted.TLabel",
            font=AppTheme.typography.field_label,
        ).pack(anchor="w", pady=(0, s.md))
        chips_row = ttk.Frame(quick_card.content, style="Surface.TFrame")
        chips_row.pack(anchor="w")

        self.paid_chip = StatusChip(chips_row, "Paid: 0")
        self.paid_chip.set_variant("success", "Paid: 0")
        self.paid_chip.pack(side="left", padx=(0, s.xs))

        self.partial_chip = StatusChip(chips_row, "Partial: 0")
        self.partial_chip.set_variant("warning", "Partial: 0")
        self.partial_chip.pack(side="left", padx=(0, s.xs))

        self.pending_chip = StatusChip(chips_row, "Pending: 0")
        self.pending_chip.set_variant("danger", "Pending: 0")
        self.pending_chip.pack(side="left")

        for col_idx in range(3):
            stats_grid.columnconfigure(col_idx, weight=1, uniform="kpi")

        # Breakdown Table Card
        breakdown_card = AppCard(
            self,
            title="Payment Status Breakdown",
            subtitle="Distribution of assigned fees across payment states",
        )
        breakdown_card.pack(fill="both", expand=True)

        self.status_table = AppTable(
            breakdown_card.content,
            columns=(
                TableColumn("status", "Status", width=220, anchor="w"),
                TableColumn("count", "Fee Records", width=160, anchor="center"),
            ),
            height=4,
        )
        self.status_table.pack(fill="both", expand=True)

    def refresh_stats(self) -> None:
        """Reload dashboard metrics from the repository."""
        stats = self.repository.get_stats()
        self.total_members_card.set_value(stats.total_members)
        self.pending_count_card.set_value(stats.pending_count)
        self.total_fees_card.set_value(format_pkr(stats.total_fees))
        self.total_paid_card.set_value(format_pkr(stats.total_paid))
        self.total_pending_card.set_value(format_pkr(stats.total_pending))

        bd = stats.status_breakdown
        self.paid_chip.set_variant("success", f"Paid: {bd.get('Paid', 0)}")
        self.partial_chip.set_variant("warning", f"Partial: {bd.get('Partial', 0)}")
        self.pending_chip.set_variant("danger", f"Pending: {bd.get('Pending', 0)}")

        rows = [(status, count) for status, count in sorted(bd.items())]
        self.status_table.set_rows(rows, tag_fn=lambda r, i: status_row_tag(str(r[0]), i))

    def _schedule_refresh(self) -> None:
        self._after_id = self.after(self.AUTO_REFRESH_MS, self._auto_refresh)

    def _auto_refresh(self) -> None:
        if not self.winfo_exists():
            return
        try:
            self.refresh_stats()
        finally:
            if self.winfo_exists():
                self._schedule_refresh()

    def _on_destroy(self, event) -> None:
        if event.widget is self and self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def export_payments(self) -> None:
        """Prompt for destination and export payment report to Excel."""
        filename = ask_save_excel(initial_filename="gym_payment_report.xlsx", parent=self)
        if not filename:
            return
        ok, msg = self.repository.export_payment_report(filename)
        if ok:
            show_info("Export Complete", msg, parent=self)
        else:
            show_error("Export Failed", msg, parent=self)
