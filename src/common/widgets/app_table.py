"""Rounded shadcn/ui Data Table wrapping ttk.Treeview and slim scrollbars."""

from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable, Literal, Optional, Sequence

from src.common.theme import AppTheme
from .canvas_primitives import draw_rounded_rect, resolve_parent_bg


@dataclass(frozen=True)
class TableColumn:
    """Column specification for AppTable."""

    key: str
    heading: str
    width: int = 110
    anchor: Literal["w", "center", "e"] = "w"
    stretch: bool = True


class AppTable(tk.Canvas):
    """Rounded dark bordered table with clean striping, semantic text, and scrollbars."""

    def __init__(
        self,
        parent,
        columns: Sequence[TableColumn],
        height: int = 12,
        horizontal_scroll: bool = False,
        on_select: Optional[Callable[[tuple], None]] = None,
        on_double_click: Optional[Callable[[tuple], None]] = None,
    ) -> None:
        c = AppTheme.colors
        parent_bg = resolve_parent_bg(parent, c.surface)
        super().__init__(parent, bg=parent_bg, bd=0, highlightthickness=0)

        self._columns = list(columns)
        col_keys = [col.key for col in self._columns]

        self._container = ttk.Frame(self, style="Surface.TFrame", padding=6)
        self._win_id = self.create_window(2, 2, anchor="nw", window=self._container)

        self.tree = ttk.Treeview(
            self._container,
            columns=col_keys,
            show="headings",
            height=height,
            selectmode="browse",
        )

        for col in self._columns:
            self.tree.heading(col.key, text=col.heading, anchor=col.anchor)
            self.tree.column(col.key, width=col.width, anchor=col.anchor, stretch=col.stretch)

        self._configure_tags()

        v_scroll = ttk.Scrollbar(self._container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        if horizontal_scroll:
            h_scroll = ttk.Scrollbar(self._container, orient="horizontal", command=self.tree.xview)
            self.tree.configure(xscrollcommand=h_scroll.set)
            h_scroll.grid(row=1, column=0, sticky="ew")

        self._container.rowconfigure(0, weight=1)
        self._container.columnconfigure(0, weight=1)

        self._container.bind("<Configure>", self._sync_from_inner)
        self.bind("<Configure>", self._on_resize)
        self._sync_from_inner()

        if on_select:
            self.tree.bind("<<TreeviewSelect>>", lambda _e: self._emit(on_select))
        if on_double_click:
            self.tree.bind("<Double-1>", lambda _e: self._emit(on_double_click))

    def _sync_from_inner(self, _event=None) -> None:
        req_w = max(180, self._container.winfo_reqwidth() + 4)
        req_h = max(120, self._container.winfo_reqheight() + 4)
        if int(float(self["height"])) != req_h or int(float(self["width"])) < req_w:
            super().configure(width=req_w, height=req_h)
        self._redraw_border()

    def _on_resize(self, event) -> None:
        w = max(80, event.width)
        h = max(80, event.height)
        self.itemconfigure(self._win_id, width=w - 4, height=h - 4)
        self._redraw_border(w, h)

    def _redraw_border(self, width: Optional[int] = None, height: Optional[int] = None) -> None:
        self.delete("table_bg")
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
            tag="table_bg",
        )
        self.tag_lower("table_bg")

    def _configure_tags(self) -> None:
        c = AppTheme.colors
        self.tree.tag_configure("even", background=c.surface, foreground=c.text_primary)
        self.tree.tag_configure("odd", background=c.surface_elevated, foreground=c.text_primary)
        self.tree.tag_configure("paid", background=c.surface, foreground=c.success_text)
        self.tree.tag_configure("partial", background=c.surface, foreground=c.warning_text)
        self.tree.tag_configure("pending", background=c.surface, foreground=c.danger_text)

    def _emit(self, callback: Callable[[tuple], None]) -> None:
        values = self.get_selected_values()
        if values is not None:
            callback(values)

    def clear(self) -> None:
        """Remove all rows from the table."""
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

    def clear_selection(self) -> None:
        """Clear any active row selection."""
        for item_id in self.tree.selection():
            self.tree.selection_remove(item_id)

    def set_rows(
        self,
        rows: Iterable[Sequence[object]],
        tag_fn: Optional[Callable[[Sequence[object], int], str]] = None,
    ) -> None:
        """Replace table rows, applying subtle dark striping or a semantic tag function."""
        self.clear()
        for idx, row in enumerate(rows):
            tag = tag_fn(row, idx) if tag_fn else ("even" if idx % 2 == 0 else "odd")
            self.tree.insert("", "end", values=tuple(row), tags=(tag,))

    def get_selected_values(self) -> Optional[tuple]:
        """Return the selected row's values tuple, or None if nothing is selected."""
        selection = self.tree.selection()
        if not selection:
            return None
        values = self.tree.item(selection[0]).get("values")
        return tuple(values) if values else None


def status_row_tag(status: str, row_index: int) -> str:
    """Return a semantic row tag for Paid/Partial/Pending, falling back to subtle striping."""
    normalized = (status or "").strip().lower()
    if normalized in ("paid", "partial", "pending"):
        return normalized
    return "even" if row_index % 2 == 0 else "odd"
