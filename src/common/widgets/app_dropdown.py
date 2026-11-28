"""Custom shadcn/ui Zinc Dark dropdown trigger and rounded popover option sheet."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Sequence

from src.common.theme import AppTheme
from .canvas_primitives import draw_rounded_rect


class _DropdownSheet(tk.Toplevel):
    """Floating rounded dark popover sheet displaying selectable dropdown options."""

    MAX_VISIBLE_ROWS = 7
    ROW_HEIGHT = 32

    def __init__(
        self,
        owner: "AppDropdown",
        options: Sequence[str],
        selected_value: str,
        x: int,
        y: int,
        width: int,
        on_pick: Callable[[str], None],
    ) -> None:
        super().__init__(owner)
        c = AppTheme.colors
        self.overrideredirect(True)
        self.configure(bg=c.background)
        self.transient(owner.winfo_toplevel())

        self._owner = owner
        self._on_pick = on_pick
        self._options = list(options)
        self._selected_value = selected_value

        visible_count = max(1, min(len(self._options), self.MAX_VISIBLE_ROWS))
        sheet_h = visible_count * self.ROW_HEIGHT + 12

        self.geometry(f"{width}x{sheet_h}+{x}+{y}")

        canvas = tk.Canvas(
            self,
            width=width,
            height=sheet_h,
            bg=c.background,
            bd=0,
            highlightthickness=0,
        )
        canvas.pack(fill="both", expand=True)
        draw_rounded_rect(
            canvas,
            1,
            1,
            width - 2,
            sheet_h - 2,
            radius=AppTheme.radius.control,
            fill=c.surface,
            outline=c.input_border,
            width=1,
        )

        inner_frame = tk.Frame(canvas, bg=c.surface)
        canvas.create_window(6, 6, anchor="nw", window=inner_frame, width=width - 12, height=sheet_h - 12)

        if not self._options:
            tk.Label(
                inner_frame,
                text="No options available",
                bg=c.surface,
                fg=c.text_muted,
                font=AppTheme.typography.caption,
                anchor="w",
                padx=10,
            ).pack(fill="both", expand=True)
        elif len(self._options) <= self.MAX_VISIBLE_ROWS:
            for opt in self._options:
                self._add_row(inner_frame, opt, width - 12)
        else:
            scroll_canvas = tk.Canvas(
                inner_frame, bg=c.surface, bd=0, highlightthickness=0
            )
            v_scroll = ttk.Scrollbar(inner_frame, orient="vertical", command=scroll_canvas.yview)
            scroll_canvas.configure(yscrollcommand=v_scroll.set)
            scroll_canvas.pack(side="left", fill="both", expand=True)
            v_scroll.pack(side="right", fill="y")

            list_holder = tk.Frame(scroll_canvas, bg=c.surface)
            row_w = width - 26
            scroll_canvas.create_window((0, 0), window=list_holder, anchor="nw", width=row_w)
            for opt in self._options:
                self._add_row(list_holder, opt, row_w)
            list_holder.update_idletasks()
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))
            scroll_canvas.bind(
                "<MouseWheel>",
                lambda e: scroll_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
            )

        self._parent_cfg_bind_id: Optional[str] = None
        self._parent_esc_bind_id: Optional[str] = None
        top = owner.winfo_toplevel()
        self._parent_cfg_bind_id = top.bind(
            "<Configure>",
            lambda e, t=top: self.close() if e.widget is t else None,
            add="+",
        )
        self._parent_esc_bind_id = top.bind("<Escape>", lambda _e: self.close(), add="+")

        self.bind("<ButtonPress-1>", self._on_global_press)
        self.update_idletasks()
        self.lift()
        try:
            self.grab_set()
        except tk.TclError:
            pass

    def close(self) -> None:
        """Release grab, unbind parent listeners, and restore focus to parent window."""
        top = self._owner.winfo_toplevel()
        if self._parent_cfg_bind_id:
            try:
                top.unbind("<Configure>", self._parent_cfg_bind_id)
            except Exception:
                pass
            self._parent_cfg_bind_id = None
        if self._parent_esc_bind_id:
            try:
                top.unbind("<Escape>", self._parent_esc_bind_id)
            except Exception:
                pass
            self._parent_esc_bind_id = None
        if self.winfo_exists():
            try:
                self.grab_release()
            except tk.TclError:
                pass
            self.destroy()
        try:
            if top.winfo_exists():
                top.focus_set()
        except tk.TclError:
            pass

    def _on_global_press(self, event) -> None:
        """Close the sheet when clicking anywhere outside its bounds."""
        if not self.winfo_exists():
            return
        sx = self.winfo_rootx()
        sy = self.winfo_rooty()
        sw = self.winfo_width()
        sh = self.winfo_height()
        if not (sx <= event.x_root <= sx + sw and sy <= event.y_root <= sy + sh):
            self.close()

    def _add_row(self, parent: tk.Frame, value: str, row_width: int) -> None:
        c = AppTheme.colors
        is_selected = value == self._selected_value

        row = tk.Canvas(
            parent,
            width=row_width,
            height=self.ROW_HEIGHT,
            bg=c.surface,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        row.pack(fill="x")

        def draw(hovered: bool) -> None:
            row.delete("all")
            if hovered or is_selected:
                fill = c.surface_muted if hovered else c.surface_elevated
                draw_rounded_rect(
                    row,
                    1,
                    1,
                    row_width - 2,
                    self.ROW_HEIGHT - 2,
                    radius=6,
                    fill=fill,
                    outline="",
                    width=0,
                )
            row.create_text(
                10,
                self.ROW_HEIGHT / 2.0,
                text=value,
                fill=c.text_primary,
                font=AppTheme.typography.body_bold if is_selected else AppTheme.typography.body,
                anchor="w",
            )
            if is_selected:
                row.create_text(
                    row_width - 12,
                    self.ROW_HEIGHT / 2.0,
                    text="✓",
                    fill=c.text_primary,
                    font=AppTheme.typography.body_bold,
                    anchor="e",
                )

        draw(False)
        row.bind("<Enter>", lambda _e: draw(True))
        row.bind("<Leave>", lambda _e: draw(False))
        row.bind("<Button-1>", lambda _e: self._pick(value))

    def _pick(self, value: str) -> None:
        self._on_pick(value)
        self.close()


class AppDropdown(ttk.Frame):
    """Themed shadcn/ui Zinc Dark dropdown with custom rounded popover sheet."""

    def __init__(
        self,
        parent,
        label: str = "",
        options: Sequence[str] = (),
        width: int = 28,
        readonly: bool = True,
        initial_value: str = "",
        placeholder: str = "Select an option...",
        surface: bool = True,
        postcommand: Optional[Callable[[], None]] = None,
        on_select: Optional[Callable[[str], None]] = None,
    ) -> None:
        c = AppTheme.colors
        frame_style = "Surface.TFrame" if surface else "TFrame"
        label_style = "FieldLabel.TLabel" if surface else "TLabel"
        super().__init__(parent, style=frame_style)

        self._items: list[str] = list(options)
        self._readonly = readonly
        self._placeholder = placeholder
        self._postcommand = postcommand
        self._on_select = on_select
        self._focused = False
        self._has_error = False
        self._sheet: Optional[_DropdownSheet] = None
        self._canvas_bg = c.surface if surface else c.background

        self.var = tk.StringVar(value=initial_value)
        self.error_var = tk.StringVar(value="")

        if label:
            self.label_widget = ttk.Label(self, text=label, style=label_style)
            self.label_widget.pack(anchor="w", pady=(0, AppTheme.spacing.xs))

        self._box = tk.Canvas(
            self,
            height=34,
            bg=self._canvas_bg,
            bd=0,
            highlightthickness=0,
            cursor="hand2" if readonly else "",
            takefocus=1 if readonly else 0,
        )
        self._box.pack(fill="x")

        if not readonly:
            self.entry = tk.Entry(
                self._box,
                textvariable=self.var,
                width=width,
                bd=0,
                highlightthickness=0,
                relief="flat",
                bg=c.surface,
                fg=c.text_primary,
                insertbackground=c.text_primary,
                selectbackground=c.surface_active,
                selectforeground=c.text_primary,
                font=AppTheme.typography.body,
            )
            self._entry_win = self._box.create_window(10, 17, anchor="w", window=self.entry)
            self.entry.bind("<FocusIn>", self._on_focus_in, add="+")
            self.entry.bind("<FocusOut>", self._on_focus_out, add="+")
            self.entry.bind("<KeyRelease>", lambda _e: self.clear_error(), add="+")
        else:
            self._entry_win = None
            self._box.bind("<FocusIn>", self._on_focus_in, add="+")
            self._box.bind("<FocusOut>", self._on_focus_out, add="+")
            self._box.bind("<Return>", lambda _e: self._toggle_sheet(), add="+")
            self._box.bind("<space>", lambda _e: self._toggle_sheet(), add="+")

        self._box.bind("<Configure>", self._on_box_resize)
        self._box.bind("<Button-1>", self._on_box_click)

        self.error_label = ttk.Label(self, textvariable=self.error_var, style="Error.TLabel")
        self._redraw_box()

    def _on_box_resize(self, event) -> None:
        w = max(60, event.width)
        h = max(34, event.height)
        if self._entry_win is not None:
            self._box.coords(self._entry_win, 10, h / 2.0)
            self._box.itemconfigure(self._entry_win, width=max(20, w - 38))
        self._redraw_box(w, h)

    def _redraw_box(self, width: Optional[int] = None, height: Optional[int] = None) -> None:
        self._box.delete("box_bg")
        w = width or max(self._box.winfo_width(), 140)
        h = height or max(self._box.winfo_height(), 34)
        c = AppTheme.colors

        sheet_open = self._sheet is not None and self._sheet.winfo_exists()
        if self._has_error:
            outline, stroke = c.danger, 1.5
        elif self._focused or sheet_open:
            outline, stroke = c.ring, 1.5
        else:
            outline, stroke = c.input_border, 1

        draw_rounded_rect(
            self._box,
            1,
            1,
            w - 2,
            h - 2,
            radius=AppTheme.radius.control,
            fill=c.surface,
            outline=outline,
            width=stroke,
            tag="box_bg",
        )

        if self._readonly:
            val = self.var.get().strip()
            display = val if val else self._placeholder
            fg = c.text_primary if val else c.text_muted
            self._box.create_text(
                12,
                h / 2.0,
                text=display,
                fill=fg,
                font=AppTheme.typography.body,
                anchor="w",
                tags=("box_bg",),
            )

        # Clean dark chevron indicator on the right (zero white clam square)
        self._box.create_text(
            w - 14,
            h / 2.0,
            text="▾",
            fill=c.text_muted,
            font=AppTheme.typography.body,
            anchor="center",
            tags=("box_bg",),
        )
        self._box.tag_lower("box_bg")

    def _on_box_click(self, event) -> None:
        if self._readonly or event.x >= max(0, self._box.winfo_width() - 32):
            self._toggle_sheet()
        elif hasattr(self, "entry"):
            self.entry.focus_set()

    def _toggle_sheet(self) -> None:
        if self._sheet is not None and self._sheet.winfo_exists():
            self._sheet.close()
            self._sheet = None
            self._redraw_box()
            return

        if self._postcommand:
            self._postcommand()

        self._box.update_idletasks()
        x = self._box.winfo_rootx()
        y = self._box.winfo_rooty() + self._box.winfo_height() + 4
        w = max(140, self._box.winfo_width())

        self._sheet = _DropdownSheet(
            self,
            options=self._items,
            selected_value=self.var.get(),
            x=x,
            y=y,
            width=w,
            on_pick=self._on_option_picked,
        )
        self._sheet.bind("<Destroy>", lambda _e: self._on_sheet_closed(), add="+")
        self._redraw_box()

    def _on_sheet_closed(self) -> None:
        self._sheet = None
        if self.winfo_exists():
            self._redraw_box()

    def _on_option_picked(self, value: str) -> None:
        self.var.set(value)
        self.clear_error()
        self._redraw_box()
        if self._on_select:
            self._on_select(value)

    def _on_focus_in(self, _event=None) -> None:
        self._focused = True
        self._redraw_box()

    def _on_focus_out(self, _event=None) -> None:
        self._focused = False
        self._redraw_box()

    def set_options(self, options: Sequence[str]) -> None:
        """Replace the dropdown option list."""
        self._items = list(options)

    def get(self) -> str:
        """Return the currently selected option."""
        return self.var.get()

    def set(self, value: str) -> None:
        """Programmatically set the dropdown value."""
        self.var.set(value)
        self.clear_error()
        self._redraw_box()

    def clear(self) -> None:
        """Reset the selected option."""
        self.var.set("")
        self.clear_error()
        self._redraw_box()

    def set_error(self, message: str) -> None:
        """Display an inline validation error message."""
        self._has_error = True
        self.error_var.set(message)
        if not self.error_label.winfo_ismapped():
            self.error_label.pack(anchor="w", pady=(2, 0))
        self._redraw_box()

    def clear_error(self) -> None:
        """Hide any active inline validation error."""
        self._has_error = False
        if self.error_var.get():
            self.error_var.set("")
        if self.error_label.winfo_ismapped():
            self.error_label.pack_forget()
        self._redraw_box()
