"""Exact-arc pure-Tkinter Canvas drawing primitives for rounded surfaces and true pills."""

import tkinter as tk


def draw_rounded_rect(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float,
    fill: str = "",
    outline: str = "",
    width: float = 1,
    tag: str = "rounded_bg",
) -> None:
    """Draw a geometrically accurate rounded rectangle or pill using ovals, rects, and arcs."""
    w = x2 - x1
    h = y2 - y1
    r = max(0.0, min(float(radius), w / 2.0, h / 2.0))
    if r <= 0.5:
        canvas.create_rectangle(
            x1, y1, x2, y2, fill=fill, outline=outline, width=width, tags=(tag,)
        )
        return

    d = 2.0 * r

    if fill:
        # Four corner circles + central horizontal & vertical rectangles
        canvas.create_oval(x1, y1, x1 + d, y1 + d, fill=fill, outline="", tags=(tag,))
        canvas.create_oval(x2 - d, y1, x2, y1 + d, fill=fill, outline="", tags=(tag,))
        canvas.create_oval(x1, y2 - d, x1 + d, y2, fill=fill, outline="", tags=(tag,))
        canvas.create_oval(x2 - d, y2 - d, x2, y2, fill=fill, outline="", tags=(tag,))
        canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="", tags=(tag,))
        canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline="", tags=(tag,))

    if outline and width > 0:
        # Four quarter-circle border arcs + four straight edge segments
        canvas.create_arc(
            x1, y1, x1 + d, y1 + d, start=90, extent=90, style="arc", outline=outline, width=width, tags=(tag,)
        )
        canvas.create_arc(
            x2 - d, y1, x2, y1 + d, start=0, extent=90, style="arc", outline=outline, width=width, tags=(tag,)
        )
        canvas.create_arc(
            x2 - d, y2 - d, x2, y2, start=270, extent=90, style="arc", outline=outline, width=width, tags=(tag,)
        )
        canvas.create_arc(
            x1, y2 - d, x1 + d, y2, start=180, extent=90, style="arc", outline=outline, width=width, tags=(tag,)
        )
        canvas.create_line(x1 + r, y1, x2 - r, y1, fill=outline, width=width, tags=(tag,))
        canvas.create_line(x1 + r, y2, x2 - r, y2, fill=outline, width=width, tags=(tag,))
        canvas.create_line(x1, y1 + r, x1, y2 - r, fill=outline, width=width, tags=(tag,))
        canvas.create_line(x2, y1 + r, x2, y2 - r, fill=outline, width=width, tags=(tag,))


def draw_pill(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    fill: str = "",
    outline: str = "",
    width: float = 1,
    tag: str = "pill_bg",
) -> None:
    """Draw a true semicircular pill (rounded-full) shape."""
    radius = max(0.0, (y2 - y1) / 2.0)
    draw_rounded_rect(
        canvas,
        x1,
        y1,
        x2,
        y2,
        radius=radius,
        fill=fill,
        outline=outline,
        width=width,
        tag=tag,
    )


def resolve_parent_bg(widget: tk.Misc, fallback: str) -> str:
    """Safely inspect parent background color so Canvas corners blend seamlessly."""
    try:
        bg = widget.cget("bg")
        if bg:
            return str(bg)
    except tk.TclError:
        pass
    try:
        bg = widget.cget("background")
        if bg:
            return str(bg)
    except tk.TclError:
        pass
    return fallback
