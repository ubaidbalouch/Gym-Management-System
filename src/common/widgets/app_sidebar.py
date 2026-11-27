"""shadcn/ui Zinc Dark Left Sidebar navigation with pill nav items."""

from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Sequence

from src.common.theme import AppTheme
from .canvas_primitives import draw_pill, draw_rounded_rect


@dataclass(frozen=True)
class SidebarNavItem:
    """Navigation route descriptor for AppSidebar."""

    key: str
    label: str
    icon: str
    group: str = "Navigation"
    subtitle: str = ""


class _SidebarItemButton(tk.Canvas):
    """Pill-shaped sidebar navigation row with dark active and hover states."""

    def __init__(
        self,
        parent,
        item: SidebarNavItem,
        selected: bool,
        on_click: Callable[[str], None],
    ) -> None:
        c = AppTheme.colors
        super().__init__(
            parent,
            height=36,
            bg=c.sidebar_bg,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self.item = item
        self._selected = selected
        self._hovered = False
        self._on_click = on_click

        self.bind("<Configure>", lambda _e: self._redraw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", lambda _e: self._on_click(self.item.key))
        self._redraw()

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._redraw()

    def _on_enter(self, _event=None) -> None:
        self._hovered = True
        self._redraw()

    def _on_leave(self, _event=None) -> None:
        self._hovered = False
        self._redraw()

    def _redraw(self) -> None:
        self.delete("all")
        w = max(self.winfo_width(), 200)
        h = max(self.winfo_height(), 36)
        c = AppTheme.colors

        if self._selected:
            fill = c.sidebar_item_active
            fg = c.sidebar_item_active_fg
            font = AppTheme.typography.body_bold
        elif self._hovered:
            fill = c.sidebar_item_hover
            fg = c.text_primary
            font = AppTheme.typography.body
        else:
            fill = c.sidebar_bg
            fg = c.text_muted
            font = AppTheme.typography.body

        if self._selected or self._hovered:
            draw_pill(
                self,
                1,
                1,
                w - 2,
                h - 2,
                fill=fill,
                outline="",
                width=0,
            )

        self.create_text(
            15,
            h / 2.0,
            text=self.item.icon,
            fill=fg,
            font=AppTheme.typography.body,
            anchor="w",
        )
        self.create_text(
            38,
            h / 2.0,
            text=self.item.label,
            fill=fg,
            font=font,
            anchor="w",
        )


class AppSidebar(tk.Frame):
    """Fixed-width shadcn/ui dark sidebar with brand header, grouped pill routes, and footer."""

    def __init__(
        self,
        parent,
        items: Sequence[SidebarNavItem],
        initial_key: Optional[str] = None,
        on_select: Optional[Callable[[str], None]] = None,
        version: str = "v2.0.0",
    ) -> None:
        c = AppTheme.colors
        s = AppTheme.spacing
        super().__init__(parent, bg=c.sidebar_bg, width=s.sidebar_width)
        self.pack_propagate(False)

        self._items = list(items)
        self._on_select = on_select
        self._selected_key = initial_key or (self._items[0].key if self._items else "")
        self._buttons: dict[str, _SidebarItemButton] = {}

        # Brand Header
        brand_bar = tk.Frame(self, bg=c.sidebar_bg, padx=s.lg, pady=14)
        brand_bar.pack(fill="x")

        logo_badge = tk.Canvas(
            brand_bar, width=32, height=32, bg=c.sidebar_bg, bd=0, highlightthickness=0
        )
        draw_rounded_rect(logo_badge, 1, 1, 30, 30, radius=9, fill=c.primary, outline="")
        logo_badge.create_text(
            15.5,
            15.5,
            text="G",
            fill=c.primary_foreground,
            font=AppTheme.typography.h3,
        )
        logo_badge.pack(side="left", padx=(0, s.sm))

        brand_text = tk.Frame(brand_bar, bg=c.sidebar_bg)
        brand_text.pack(side="left", fill="x")
        tk.Label(
            brand_text,
            text="GymOS",
            bg=c.sidebar_bg,
            fg=c.text_primary,
            font=AppTheme.typography.h3,
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            brand_text,
            text="Management Suite",
            bg=c.sidebar_bg,
            fg=c.text_muted,
            font=AppTheme.typography.caption,
            anchor="w",
        ).pack(anchor="w")

        tk.Frame(self, bg=c.sidebar_border, height=1).pack(fill="x")

        # Grouped Pill Navigation List
        nav_body = tk.Frame(self, bg=c.sidebar_bg, padx=s.md, pady=s.md)
        nav_body.pack(fill="both", expand=True)

        current_group: Optional[str] = None
        for item in self._items:
            if item.group != current_group:
                top_pad = 0 if current_group is None else s.md
                tk.Label(
                    nav_body,
                    text=item.group.upper(),
                    bg=c.sidebar_bg,
                    fg=c.text_muted,
                    font=AppTheme.typography.sidebar_section,
                    anchor="w",
                ).pack(fill="x", padx=s.sm, pady=(top_pad, s.xs))
                current_group = item.group

            btn = _SidebarItemButton(
                nav_body,
                item=item,
                selected=(item.key == self._selected_key),
                on_click=self.select,
            )
            btn.pack(fill="x", pady=2)
            self._buttons[item.key] = btn

        # Footer Status
        tk.Frame(self, bg=c.sidebar_border, height=1).pack(fill="x")
        footer = tk.Frame(self, bg=c.sidebar_bg, padx=s.lg, pady=s.md)
        footer.pack(fill="x", side="bottom")

        status_row = tk.Frame(footer, bg=c.sidebar_bg)
        status_row.pack(fill="x")
        dot = tk.Canvas(
            status_row, width=10, height=10, bg=c.sidebar_bg, bd=0, highlightthickness=0
        )
        dot.create_oval(2, 2, 8, 8, fill=c.success, outline="")
        dot.pack(side="left", padx=(0, s.xs))
        ttk.Label(status_row, text="SQLite Connected", style="StatusOk.TLabel").pack(side="left")

        tk.Label(
            footer,
            text=f"{version} · Currency: PKR",
            bg=c.sidebar_bg,
            fg=c.text_muted,
            font=AppTheme.typography.caption,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

    def select(self, key: str, notify: bool = True) -> None:
        """Select a navigation route and notify parent shell."""
        if key not in self._buttons:
            return
        self._selected_key = key
        for btn_key, btn in self._buttons.items():
            btn.set_selected(btn_key == key)
        if notify and self._on_select:
            self._on_select(key)

    def get_selected(self) -> str:
        """Return active route key."""
        return self._selected_key
