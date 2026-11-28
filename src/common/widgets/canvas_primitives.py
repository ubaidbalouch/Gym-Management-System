"""Smooth Canvas primitives for rounded rectangles and concentric RoundCap pills."""

import math
import tkinter as tk


def _rounded_rect_points(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float,
    segments: int = 24,
) -> list[float]:
    """Generate high-density circular-arc polygon vertices for a rounded rectangle."""
    w = x2 - x1
    h = y2 - y1
    r = max(0.0, min(float(radius), w / 2.0, h / 2.0))
    if r <= 0.5:
        return [x1, y1, x2, y1, x2, y2, x1, y2]

    pts: list[float] = []
    corners = (
        (x2 - r, y1 + r, -math.pi / 2.0, 0.0),          # top-right
        (x2 - r, y2 - r, 0.0, math.pi / 2.0),           # bottom-right
        (x1 + r, y2 - r, math.pi / 2.0, math.pi),       # bottom-left
        (x1 + r, y1 + r, math.pi, 1.5 * math.pi),       # top-left
    )
    for cx, cy, start_a, end_a in corners:
        for i in range(segments + 1):
            theta = start_a + (end_a - start_a) * (i / segments)
            pts.append(cx + r * math.cos(theta))
            pts.append(cy + r * math.sin(theta))
    return pts


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
) -> int:
    """Draw a smooth rounded rectangle using a high-density circular-arc polygon."""
    pts = _rounded_rect_points(x1, y1, x2, y2, radius=radius, segments=24)
    return canvas.create_polygon(
        pts,
        fill=fill,
        outline=outline,
        width=width if outline else 0,
        tags=(tag,),
    )


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
) -> int:
    """Draw a smooth semicircular pill using concentric native RoundCap strokes."""
    h = max(4.0, y2 - y1)
    r = h / 2.0
    cy = (y1 + y2) / 2.0
    lx = x1 + r
    rx = max(lx, x2 - r)

    item_id = 0
    if outline and width > 0:
        item_id = canvas.create_line(
            lx,
            cy,
            rx,
            cy,
            width=h,
            capstyle=tk.ROUND,
            fill=outline,
            tags=(tag,),
        )
        inner_w = max(2.0, h - 2.0 * width)
        if fill:
            item_id = canvas.create_line(
                lx,
                cy,
                rx,
                cy,
                width=inner_w,
                capstyle=tk.ROUND,
                fill=fill,
                tags=(tag,),
            )
    elif fill:
        item_id = canvas.create_line(
            lx,
            cy,
            rx,
            cy,
            width=h,
            capstyle=tk.ROUND,
            fill=fill,
            tags=(tag,),
        )
    return item_id


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
