"""Main application shell wiring shadcn/ui sidebar, theme, repositories, and feature views."""

import os
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from src.common.database import DatabaseConnection, initialize_schema
from src.common.theme import AppTheme, enable_high_dpi_awareness
from src.common.widgets import AppChip, AppSidebar, SidebarNavItem, ask_confirm, show_error
from src.features.dashboard.dashboard_repository import DashboardRepository
from src.features.dashboard.dashboard_view import DashboardView
from src.features.fees.fee_repository import FeeRepository
from src.features.fees.member_fees_view import MemberFeesView
from src.features.help.help_view import HelpView
from src.features.members.member_management_view import MemberManagementView
from src.features.members.member_repository import MemberRepository
from src.features.payments.payment_history_view import PaymentHistoryView
from src.features.payments.payment_management_view import PaymentManagementView
from src.features.payments.payment_repository import PaymentRepository
from src.features.search.search_repository import SearchRepository
from src.features.search.search_view import SearchView

NAV_ITEMS: tuple[SidebarNavItem, ...] = (
    SidebarNavItem("dashboard", "Dashboard", "▣", "Overview", "Financial metrics and status overview"),
    SidebarNavItem("members", "Members", "◎", "Operations", "Register, edit, and inspect gym members"),
    SidebarNavItem("fees", "Member Fees", "▤", "Operations", "Assigned fees and status filter ledger"),
    SidebarNavItem("payments", "Payments (PKR)", "◈", "Operations", "Assign fees and record PKR payments"),
    SidebarNavItem("history", "Payment History", "◷", "Operations", "Chronological fee and payment records"),
    SidebarNavItem("search", "Search & Reports", "⌕", "Insights", "Find members and export statements"),
    SidebarNavItem("help", "Help & Guide", "?", "Insights", "Quick reference and workflow guide"),
)


class GymManagementApp:
    """Root desktop application shell with shadcn/ui sidebar and stacked feature views."""

    APP_VERSION = "v2.0.0"

    def __init__(self, db_path: Optional[str] = None) -> None:
        enable_high_dpi_awareness()
        self.root = tk.Tk()
        self.root.title("GymOS — Gym Management Software")
        self.root.geometry("1280x820")
        self.root.minsize(1060, 660)

        self._apply_window_icon()
        AppTheme.apply(self.root)

        self.db = DatabaseConnection(db_path=db_path)
        initialize_schema(self.db)

        self.member_repo = MemberRepository(self.db)
        self.fee_repo = FeeRepository(self.db)
        self.payment_repo = PaymentRepository(self.db)
        self.dashboard_repo = DashboardRepository(self.db)
        self.search_repo = SearchRepository(self.db)

        self._route_meta = {item.key: item for item in NAV_ITEMS}
        self._views: dict[str, ttk.Frame] = {}
        self._refresh_handlers: dict[str, Callable[[], None]] = {}

        self._setup_ui()
        self._center_window()

    def _apply_window_icon(self) -> None:
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logo.ico"))
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except tk.TclError:
                pass

    def _setup_ui(self) -> None:
        c = AppTheme.colors
        s = AppTheme.spacing

        shell = tk.Frame(self.root, bg=c.background)
        shell.pack(fill="both", expand=True)

        # Left Sidebar
        self.sidebar = AppSidebar(
            shell,
            items=NAV_ITEMS,
            initial_key="dashboard",
            on_select=self.select_route,
            version=self.APP_VERSION,
        )
        self.sidebar.pack(side="left", fill="y")

        # Hairline vertical divider
        tk.Frame(shell, bg=c.sidebar_border, width=1).pack(side="left", fill="y")

        # Main Workspace Column
        workspace = tk.Frame(shell, bg=c.background)
        workspace.pack(side="left", fill="both", expand=True)

        # Top Bar (seamless dark zinc-950 header with hairline divider)
        topbar = tk.Frame(workspace, bg=c.background, height=s.topbar_height)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        topbar_inner = tk.Frame(topbar, bg=c.background, padx=s.xl)
        topbar_inner.pack(fill="both", expand=True)

        title_stack = tk.Frame(topbar_inner, bg=c.background)
        title_stack.pack(side="left", anchor="center")

        self.topbar_title_var = tk.StringVar(value="Dashboard")
        self.topbar_subtitle_var = tk.StringVar(value=self._route_meta["dashboard"].subtitle)

        ttk.Label(title_stack, textvariable=self.topbar_title_var, style="TopbarTitle.TLabel").pack(
            anchor="w"
        )
        ttk.Label(
            title_stack, textvariable=self.topbar_subtitle_var, style="Muted.TLabel"
        ).pack(anchor="w")

        AppChip(topbar_inner, text="Currency: PKR", variant="neutral").pack(
            side="right", anchor="center"
        )

        tk.Frame(workspace, bg=c.border, height=1).pack(fill="x")

        # Stacked Feature Content Area
        self.content_area = tk.Frame(workspace, bg=c.background)
        self.content_area.pack(fill="both", expand=True)
        self.content_area.rowconfigure(0, weight=1)
        self.content_area.columnconfigure(0, weight=1)

        self._create_views()
        self.select_route("dashboard")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_views(self) -> None:
        self.dashboard_view = DashboardView(self.content_area, self.dashboard_repo)
        self.member_view = MemberManagementView(
            self.content_area,
            member_repo=self.member_repo,
            fee_repo=self.fee_repo,
            on_data_changed=self.refresh_all,
        )
        self.fees_view = MemberFeesView(self.content_area, self.fee_repo)
        self.payment_view = PaymentManagementView(
            self.content_area,
            member_repo=self.member_repo,
            fee_repo=self.fee_repo,
            payment_repo=self.payment_repo,
            on_data_changed=self.refresh_all,
        )
        self.history_view = PaymentHistoryView(self.content_area, self.payment_repo)
        self.search_view = SearchView(self.content_area, self.search_repo, self.fee_repo)
        self.help_view = HelpView(self.content_area)

        self._views = {
            "dashboard": self.dashboard_view,
            "members": self.member_view,
            "fees": self.fees_view,
            "payments": self.payment_view,
            "history": self.history_view,
            "search": self.search_view,
            "help": self.help_view,
        }
        self._refresh_handlers = {
            "dashboard": self.dashboard_view.refresh_stats,
            "members": self.member_view.refresh_members_list,
            "fees": self.fees_view.refresh_fees_list,
            "payments": self.payment_view.populate_dropdowns,
            "history": self.history_view.refresh_history,
            "search": self.search_view.search_members,
        }

        for view in self._views.values():
            view.grid(row=0, column=0, sticky="nsew")

    def select_route(self, key: str) -> None:
        """Switch the active view, update the top bar header, and refresh data."""
        view = self._views.get(key)
        meta = self._route_meta.get(key)
        if not view or not meta:
            return

        if self.sidebar.get_selected() != key:
            self.sidebar.select(key, notify=False)

        self.topbar_title_var.set(meta.label)
        self.topbar_subtitle_var.set(meta.subtitle)
        view.tkraise()

        handler = self._refresh_handlers.get(key)
        if handler:
            handler()

    def refresh_all(self) -> None:
        """Synchronize all data-driven views after any create/update/delete/payment."""
        for handler in self._refresh_handlers.values():
            handler()

    def _center_window(self) -> None:
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = max(0, (self.root.winfo_screenwidth() // 2) - (width // 2))
        y = max(0, (self.root.winfo_screenheight() // 2) - (height // 2))
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def on_closing(self) -> None:
        """Confirm before closing the application."""
        if ask_confirm("Quit", "Are you sure you want to quit the application?", parent=self.root):
            self.root.destroy()

    def run(self) -> None:
        """Start the Tkinter event loop."""
        try:
            self.root.mainloop()
        except Exception as exc:
            show_error("Application Error", f"An unexpected error occurred:\n{exc}")


def main() -> None:
    """Application entrypoint."""
    enable_high_dpi_awareness()
    try:
        app = GymManagementApp()
        app.run()
    except Exception as exc:
        show_error("Startup Error", f"Failed to start application:\n{exc}")
