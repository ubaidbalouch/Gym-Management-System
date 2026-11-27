"""Rounded shadcn/ui Zinc Dark Card and KPI StatCard widgets."""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from src.common.theme import AppTheme
from .app_chip import AppChip
from .canvas_primitives import draw_rounded_rect, resolve_parent_bg


class AppCard(tk.Canvas):
    """Rounded elevated dark surface card with 1px zinc-800 hairline border."""

    def __init__(
        self,
        parent,
        title: str = "",
        subtitle: str = "",
        padding: Optional[int] = None,
    ) -> None:
        c = AppTheme.colors
        s = AppTheme.spacing
        pad = s.lg if padding is None else padding
        parent_bg = resolve_parent_bg(parent, c.background)

        super().__init__(
            parent,
            bg=parent_bg,
            bd=0,
            highlightthickness=0,
        )

        self.inner = ttk.Frame(self, style="Surface.TFrame", padding=pad)
        self._window_id = self.create_window(3, 3, anchor="nw", window=self.inner)

        if title or subtitle:
            header = ttk.Frame(self.inner, style="Surface.TFrame")
            header.pack(fill="x", pady=(0, s.sm))
            if title:
                ttk.Label(header, text=title, style="Section.TLabel").pack(anchor="w")
            if subtitle:
                ttk.Label(header, text=subtitle, style="SurfaceMuted.TLabel").pack(
                    anchor="w", pady=(2, 0)
                )
            ttk.Separator(self.inner, orient="horizontal").pack(fill="x", pady=(0, s.md))

        self.content = ttk.Frame(self.inner, style="Surface.TFrame")
        self.content.pack(fill="both", expand=True)

        self.inner.bind("<Configure>", self._sync_from_inner)
        self.bind("<Configure>", self._on_canvas_resize)
        self._sync_from_inner()

    def _sync_from_inner(self, _event=None) -> None:
        req_w = max(120, self.inner.winfo_reqwidth() + 6)
        req_h = max(48, self.inner.winfo_reqheight() + 6)
        if int(float(self["height"])) != req_h or int(float(self["width"])) < req_w:
            super().configure(width=req_w, height=req_h)
        self._redraw_border()

    def _on_canvas_resize(self, event) -> None:
        w = max(40, event.width)
        req_h = max(48, self.inner.winfo_reqheight() + 6)
        h = max(40, event.height, req_h)
        # Use height=0 (natural height) unless parent expanded card beyond content height
        win_h = (h - 6) if event.height > req_h else 0
        self.itemconfigure(self._window_id, width=w - 6, height=win_h)
        self._redraw_border(w, h)

    def _redraw_border(self, width: Optional[int] = None, height: Optional[int] = None) -> None:
        self.delete("card_bg")
        w = width or max(self.winfo_width(), int(float(self["width"])))
        h = height or max(self.winfo_height(), int(float(self["height"])))
        c = AppTheme.colors
        draw_rounded_rect(
            self,
            1,
            1,
            w - 2,
            h - 2,
            radius=AppTheme.radius.card,
            fill=c.surface,
            outline=c.border,
            width=1,
            tag="card_bg",
        )
        self.tag_lower("card_bg")


class StatCard(AppCard):
    """shadcn/ui Dashboard KPI card with title, crisp monochrome metric, and pill badge."""

    def __init__(
        self,
        parent,
        title: str,
        initial_value: str = "0",
        caption: str = "",
        badge_text: str = "",
        dot_color: Optional[str] = None,
    ) -> None:
        super().__init__(parent, padding=AppTheme.spacing.lg)
        c = AppTheme.colors
        s = AppTheme.spacing

        top_row = ttk.Frame(self.content, style="Surface.TFrame")
        top_row.pack(fill="x")

        ttk.Label(
            top_row,
            text=title,
            style="SurfaceMuted.TLabel",
            font=AppTheme.typography.field_label,
        ).pack(side="left")

        if badge_text:
            AppChip(top_row, text=badge_text, variant="neutral").pack(side="right")

        self.value_var = tk.StringVar(value=initial_value)
        self.value_label = tk.Label(
            self.content,
            textvariable=self.value_var,
            bg=c.surface,
            fg=c.text_primary,
            font=AppTheme.typography.stat_value,
            anchor="w",
        )
        self.value_label.pack(anchor="w", pady=(s.sm, 2))

        self.caption_var = tk.StringVar(value=caption)
        if caption or dot_color:
            cap_row = ttk.Frame(self.content, style="Surface.TFrame")
            cap_row.pack(anchor="w")
            if dot_color:
                dot = tk.Canvas(
                    cap_row, width=10, height=10, bg=c.surface, bd=0, highlightthickness=0
                )
                dot.create_oval(2, 2, 8, 8, fill=dot_color, outline="")
                dot.pack(side="left", padx=(0, s.xs))
            ttk.Label(
                cap_row,
                textvariable=self.caption_var,
                style="SurfaceMuted.TLabel",
            ).pack(side="left")

    def set_value(self, value: object, caption: Optional[str] = None) -> None:
        """Update displayed metric value and optional subtitle."""
        self.value_var.set(str(value))
        if caption is not None:
            self.caption_var.set(caption)
