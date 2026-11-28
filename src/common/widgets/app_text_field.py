"""Rounded shadcn/ui labeled text input with focus ring and inline error support."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from src.common.theme import AppTheme
from .app_button import AppButton
from .canvas_primitives import draw_rounded_rect


class AppTextField(ttk.Frame):
    """Themed labeled input wrapped in a rounded Canvas border with focus ring."""

    def __init__(
        self,
        parent,
        label: str = "",
        width: int = 28,
        readonly: bool = False,
        placeholder: str = "",
        initial_value: str = "",
        surface: bool = True,
        action_text: Optional[str] = None,
        on_action: Optional[Callable[[], None]] = None,
        on_submit: Optional[Callable[[], None]] = None,
    ) -> None:
        c = AppTheme.colors
        frame_style = "Surface.TFrame" if surface else "TFrame"
        label_style = "FieldLabel.TLabel" if surface else "TLabel"
        super().__init__(parent, style=frame_style)

        self._readonly = readonly
        self._placeholder = placeholder
        self._showing_placeholder = False
        self._focused = False
        self._has_error = False
        self._canvas_bg = c.surface if surface else c.background

        self.var = tk.StringVar(value=initial_value)
        self.error_var = tk.StringVar(value="")

        if label:
            self.label_widget = ttk.Label(self, text=label, style=label_style)
            self.label_widget.pack(anchor="w", pady=(0, AppTheme.spacing.xs))

        input_row = ttk.Frame(self, style=frame_style)
        input_row.pack(fill="x")

        self._box = tk.Canvas(
            input_row,
            height=34,
            bg=self._canvas_bg,
            bd=0,
            highlightthickness=0,
            cursor="xterm" if not readonly else "",
        )
        self._box.pack(side="left", fill="x", expand=True)

        c = AppTheme.colors
        entry_bg = c.surface_muted if readonly else c.surface
        entry_fg = c.text_muted if readonly else c.text_primary
        entry_state = "readonly" if readonly else "normal"
        self.entry = tk.Entry(
            self._box,
            textvariable=self.var,
            width=width,
            state=entry_state,
            bd=0,
            highlightthickness=0,
            relief="flat",
            bg=entry_bg,
            fg=entry_fg,
            readonlybackground=c.surface_muted,
            disabledbackground=c.surface_muted,
            disabledforeground=c.text_muted,
            insertbackground=c.text_primary,
            selectbackground=c.surface_active,
            selectforeground=c.text_primary,
            font=AppTheme.typography.body,
        )
        self._entry_win = self._box.create_window(10, 17, anchor="w", window=self.entry)

        self._box.bind("<Configure>", self._on_box_resize)
        if not readonly:
            self._box.bind("<Button-1>", self._on_box_click, add="+")
        self.entry.bind("<FocusIn>", self._on_focus_in, add="+")
        self.entry.bind("<FocusOut>", self._on_focus_out, add="+")

        if action_text and on_action:
            self.action_button = AppButton(
                input_row,
                text=action_text,
                command=on_action,
                variant="outline",
                width=3,
                height=34,
            )
            self.action_button.pack(side="left", padx=(AppTheme.spacing.xs, 0))

        self.error_label = ttk.Label(self, textvariable=self.error_var, style="Error.TLabel")

        if not readonly:
            self.entry.bind("<KeyRelease>", self._on_key_release, add="+")

        if placeholder and not readonly and not initial_value:
            self._apply_placeholder()

        if on_submit and not readonly:
            self.entry.bind("<Return>", lambda _e: on_submit(), add="+")

        self._redraw_box()

    def _on_box_resize(self, event) -> None:
        w = max(40, event.width)
        h = max(34, event.height)
        self._box.coords(self._entry_win, 10, h / 2.0)
        self._box.itemconfigure(self._entry_win, width=max(20, w - 20))
        self._redraw_box(w, h)

    def _redraw_box(self, width: Optional[int] = None, height: Optional[int] = None) -> None:
        self._box.delete("box_bg")
        w = width or max(self._box.winfo_width(), 120)
        h = height or max(self._box.winfo_height(), 34)
        c = AppTheme.colors

        fill = c.surface_muted if self._readonly else c.surface
        if self._has_error:
            outline = c.danger
            stroke = 1.5
        elif self._focused and not self._readonly:
            outline = c.ring
            stroke = 1.5
        else:
            outline = c.input_border
            stroke = 1

        draw_rounded_rect(
            self._box,
            1,
            1,
            w - 2,
            h - 2,
            radius=AppTheme.radius.control,
            fill=fill,
            outline=outline,
            width=stroke,
            tag="box_bg",
        )
        self._box.tag_lower("box_bg")

    def _apply_placeholder(self) -> None:
        self._showing_placeholder = True
        self.var.set(self._placeholder)
        self.entry.configure(foreground=AppTheme.colors.text_muted)

    def _clear_placeholder(self) -> None:
        if self._showing_placeholder:
            self._showing_placeholder = False
            self.var.set("")
            self.entry.configure(foreground=AppTheme.colors.text_primary)

    def _on_box_click(self, _event=None) -> None:
        if not self._readonly:
            self._clear_placeholder()
            self.entry.focus_set()

    def _on_focus_in(self, _event=None) -> None:
        self._focused = True
        if not self._readonly:
            self._clear_placeholder()
        self._redraw_box()

    def _on_key_release(self, _event=None) -> None:
        if self._showing_placeholder:
            self._showing_placeholder = False
            self.entry.configure(foreground=AppTheme.colors.text_primary)
        if self._has_error and self.get().strip():
            self.clear_error()

    def _on_focus_out(self, _event=None) -> None:
        self._focused = False
        if self._placeholder and not self._readonly and not self.var.get():
            self._apply_placeholder()
        self._redraw_box()

    def get(self) -> str:
        """Return the current text value (excluding placeholder text)."""
        if self._showing_placeholder:
            return ""
        return self.var.get()

    def set(self, value: object) -> None:
        """Set the text value programmatically without altering readonly protection."""
        text = "" if value is None else str(value)
        if text:
            self._showing_placeholder = False
            self.entry.configure(foreground=AppTheme.colors.text_primary)
            self.var.set(text)
        else:
            self.clear()
        self.clear_error()

    def clear(self) -> None:
        """Clear field contents and restore placeholder if configured."""
        self.var.set("")
        self._showing_placeholder = False
        self.clear_error()
        if self._placeholder and not self._readonly:
            self._apply_placeholder()

    def set_error(self, message: str) -> None:
        """Display an inline validation error message below the input."""
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

    def focus(self) -> None:
        """Focus the underlying entry widget."""
        self.entry.focus_set()
