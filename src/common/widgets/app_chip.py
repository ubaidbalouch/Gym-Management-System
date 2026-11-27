"""True semicircular pill badges, semantic status pills, and pill filter groups."""

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable, Literal, Optional, Sequence

from src.common.theme import AppTheme
from .canvas_primitives import draw_pill, resolve_parent_bg

ChipVariant = Literal["neutral", "primary", "success", "warning", "danger", "info"]


def _chip_palette(variant: ChipVariant, selected: bool = False) -> tuple[str, str, str, Optional[str]]:
    """Return (bg, fg, border, dot_color) for a dark-mode pill chip."""
    c = AppTheme.colors
    if selected:
        return c.primary, c.primary_foreground, c.primary, None

    mapping: dict[str, tuple[str, str, str, Optional[str]]] = {
        "neutral": (c.surface_muted, c.text_secondary, c.input_border, None),
        "primary": (c.primary, c.primary_foreground, c.primary, None),
        "success": (c.success_bg, c.success_text, c.success_border, c.success),
        "warning": (c.warning_bg, c.warning_text, c.warning_border, c.warning),
        "danger": (c.danger_bg, c.danger_text, c.danger_border, c.danger),
        "info": (c.info_bg, c.info_text, c.info_border, c.info),
    }
    return mapping.get(variant, mapping["neutral"])


class AppChip(tk.Canvas):
    """True rounded-full pill badge / selectable filter pill."""

    def __init__(
        self,
        parent,
        text: str,
        variant: ChipVariant = "neutral",
        selectable: bool = False,
        selected: bool = False,
        show_dot: bool = False,
        on_click: Optional[Callable[[], None]] = None,
    ) -> None:
        self._text = text
        self._variant: ChipVariant = variant
        self._selectable = selectable
        self._selected = selected
        self._show_dot = show_dot
        self._on_click = on_click
        self._parent_bg = resolve_parent_bg(parent, AppTheme.colors.surface)

        self._font = tkfont.Font(font=AppTheme.typography.chip)
        w, h = self._measure_size()

        super().__init__(
            parent,
            width=w,
            height=h,
            bg=self._parent_bg,
            bd=0,
            highlightthickness=0,
            cursor="hand2" if (selectable or on_click) else "",
        )
        self.label = self

        self._redraw()
        if selectable or on_click:
            self.bind("<Button-1>", self._handle_click)

    def _measure_size(self) -> tuple[int, int]:
        dot_space = 12 if self._show_dot else 0
        width = max(52, self._font.measure(self._text) + 26 + dot_space)
        return width, 28

    def _redraw(self) -> None:
        self.delete("all")
        w, h = self._measure_size()
        super().configure(width=w, height=h)

        bg, fg, border, dot_color = _chip_palette(self._variant, self._selected)
        if self._selectable and not self._selected:
            bg = AppTheme.colors.surface_muted
            fg = AppTheme.colors.text_muted
            border = ""

        draw_pill(
            self,
            1,
            1,
            w - 2,
            h - 2,
            fill=bg,
            outline=border,
            width=1 if border else 0,
        )

        text_x = w / 2.0
        if self._show_dot and dot_color:
            dot_x = 13
            self.create_oval(dot_x - 3, h / 2 - 3, dot_x + 3, h / 2 + 3, fill=dot_color, outline="")
            text_x = (w + 10) / 2.0

        self.create_text(
            text_x,
            h / 2.0,
            text=self._text,
            fill=fg,
            font=AppTheme.typography.chip,
            anchor="center",
        )

    def _handle_click(self, _event=None) -> None:
        if self._on_click:
            self._on_click()

    def set_selected(self, selected: bool) -> None:
        """Update active visual styling for selectable filter pills."""
        self._selected = selected
        self._redraw()

    def set_variant(self, variant: ChipVariant, text: Optional[str] = None) -> None:
        """Update pill variant colors and optional text."""
        self._variant = variant
        if text is not None:
            self._text = text
        self._redraw()

    def cget(self, key: str):
        if key == "text":
            return self._text
        return super().cget(key)


class StatusChip(AppChip):
    """Semantic status pill with dot indicator mapping Paid / Partial / Pending / No Fees."""

    _STATUS_VARIANTS: dict[str, ChipVariant] = {
        "paid": "success",
        "partial": "warning",
        "pending": "danger",
        "no fees": "neutral",
    }

    def __init__(self, parent, status: str = "Pending") -> None:
        variant = self._STATUS_VARIANTS.get(status.strip().lower(), "neutral")
        super().__init__(parent, text=status, variant=variant, show_dot=True)

    def set_status(self, status: str) -> None:
        """Update displayed status text and semantic variant."""
        variant = self._STATUS_VARIANTS.get(status.strip().lower(), "neutral")
        self.set_variant(variant, text=status)


class AppChipGroup(tk.Canvas):
    """shadcn/ui segmented rounded-full pill filter track."""

    def __init__(
        self,
        parent,
        options: Sequence[tuple[str, str]],
        initial_key: Optional[str] = None,
        on_change: Optional[Callable[[str], None]] = None,
        surface: bool = False,
    ) -> None:
        c = AppTheme.colors
        parent_bg = resolve_parent_bg(parent, c.surface if surface else c.background)
        super().__init__(parent, bg=parent_bg, bd=0, highlightthickness=0, height=36)

        self._on_change = on_change
        self._selected_key = initial_key or (options[0][0] if options else "")
        self._chips: dict[str, AppChip] = {}

        track = tk.Frame(self, bg=c.surface_muted)
        self._track_win = self.create_window(4, 4, anchor="nw", window=track)

        for key, label in options:
            chip = AppChip(
                track,
                text=label,
                variant="neutral",
                selectable=True,
                selected=(key == self._selected_key),
                on_click=lambda k=key: self.select(k),
            )
            chip.pack(side="left", padx=2)
            self._chips[key] = chip

        track.bind("<Configure>", lambda _e: self._sync_track(track))
        self._sync_track(track)

    def _sync_track(self, track: tk.Frame) -> None:
        req_w = max(90, track.winfo_reqwidth() + 8)
        req_h = max(36, track.winfo_reqheight() + 8)
        super().configure(width=req_w, height=req_h)
        self.delete("track_bg")
        draw_pill(
            self,
            1,
            1,
            req_w - 2,
            req_h - 2,
            fill=AppTheme.colors.surface_muted,
            outline=AppTheme.colors.border,
            width=1,
            tag="track_bg",
        )
        self.tag_lower("track_bg")

    def select(self, key: str, notify: bool = True) -> None:
        """Select a pill by key and optionally invoke on_change."""
        if key not in self._chips:
            return
        self._selected_key = key
        for chip_key, chip in self._chips.items():
            chip.set_selected(chip_key == key)
        if notify and self._on_change:
            self._on_change(key)

    def get_selected(self) -> str:
        """Return the currently selected pill key."""
        return self._selected_key
