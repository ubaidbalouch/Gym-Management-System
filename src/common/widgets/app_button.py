"""Rounded Canvas-backed shadcn/ui Zinc Dark button widget."""

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable, Literal, Optional

from src.common.theme import AppTheme
from .canvas_primitives import draw_pill, draw_rounded_rect, resolve_parent_bg

ButtonVariant = Literal["primary", "outline", "secondary", "danger", "ghost"]


def _variant_colors(
    variant: ButtonVariant, hovered: bool, pressed: bool, disabled: bool, parent_bg: str
) -> tuple[str, str, str]:
    """Return (fill, border, text_color) for a shadcn/ui Zinc Dark button variant."""
    c = AppTheme.colors
    if disabled:
        return c.surface_muted, c.border, c.text_muted

    if variant == "primary":
        fill = c.primary_pressed if pressed else (c.primary_hover if hovered else c.primary)
        return fill, fill, c.primary_foreground
    if variant == "outline":
        fill = c.surface_active if pressed else (c.surface_hover if hovered else c.surface)
        return fill, c.input_border, c.text_primary
    if variant == "secondary":
        fill = c.surface_active if pressed else (c.secondary_hover if hovered else c.secondary)
        return fill, c.border, c.secondary_foreground
    if variant == "danger":
        fill = c.danger_pressed if pressed else (c.danger_hover if hovered else c.danger)
        return fill, fill, c.danger_foreground
    # ghost
    fill = c.surface_active if pressed else (c.surface_hover if hovered else parent_bg)
    return fill, "", (c.text_primary if hovered else c.text_muted)


class AppButton(tk.Canvas):
    """Rounded or pill-shaped button supporting primary, outline, secondary, danger, and ghost."""

    def __init__(
        self,
        parent,
        text: str,
        command: Optional[Callable[[], None]] = None,
        variant: ButtonVariant = "primary",
        width: Optional[int] = None,
        height: int = 34,
        pill: bool = False,
        state: str = "normal",
    ) -> None:
        self._text = text
        self._command = command
        self._variant: ButtonVariant = variant
        self._pill = pill
        self._state = state
        self._hovered = False
        self._pressed = False
        self._parent_bg = resolve_parent_bg(parent, AppTheme.colors.surface)

        font_obj = tkfont.Font(font=AppTheme.typography.button)
        extra = 34 if pill else 28
        if width is not None:
            px_width = max(40, width * 9 + 16)
        else:
            px_width = max(80, font_obj.measure(text) + extra)

        super().__init__(
            parent,
            width=px_width,
            height=height,
            bg=self._parent_bg,
            bd=0,
            highlightthickness=0,
            cursor="hand2" if state != "disabled" else "arrow",
            takefocus=1,
        )

        self._redraw()
        self.bind("<Configure>", lambda _e: self._redraw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Return>", lambda _e: self.invoke())
        self.bind("<space>", lambda _e: self.invoke())

    def _redraw(self) -> None:
        self.delete("all")
        w = max(self.winfo_width(), int(self["width"]))
        h = max(self.winfo_height(), int(self["height"]))
        fill, outline, fg = _variant_colors(
            self._variant,
            hovered=self._hovered,
            pressed=self._pressed,
            disabled=(self._state == "disabled"),
            parent_bg=self._parent_bg,
        )
        if self._pill:
            draw_pill(self, 1, 1, w - 2, h - 2, fill=fill, outline=outline, width=1 if outline else 0)
        else:
            draw_rounded_rect(
                self,
                1,
                1,
                w - 2,
                h - 2,
                radius=AppTheme.radius.control,
                fill=fill,
                outline=outline,
                width=1 if outline else 0,
            )
        self.create_text(
            w / 2.0,
            h / 2.0,
            text=self._text,
            fill=fg,
            font=AppTheme.typography.button,
            anchor="center",
        )

    def _on_enter(self, _event=None) -> None:
        if self._state != "disabled":
            self._hovered = True
            self._redraw()

    def _on_leave(self, _event=None) -> None:
        self._hovered = False
        self._pressed = False
        self._redraw()

    def _on_press(self, _event=None) -> None:
        if self._state != "disabled":
            self._pressed = True
            self._redraw()

    def _on_release(self, event=None) -> None:
        was_pressed = self._pressed
        self._pressed = False
        self._redraw()
        if was_pressed and self._state != "disabled":
            if event is None or (0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height()):
                self.invoke()

    def invoke(self) -> None:
        """Execute button command if enabled."""
        if self._state != "disabled" and self._command:
            self._command()

    def configure(self, cnf=None, **kwargs):
        if "text" in kwargs:
            self._text = str(kwargs.pop("text"))
        if "state" in kwargs:
            self._state = str(kwargs.pop("state"))
            kwargs["cursor"] = "hand2" if self._state != "disabled" else "arrow"
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        result = super().configure(cnf, **kwargs) if (cnf or kwargs) else None
        self._redraw()
        return result

    config = configure

    def cget(self, key: str):
        if key == "text":
            return self._text
        if key == "state":
            return self._state
        return super().cget(key)
