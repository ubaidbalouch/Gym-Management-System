"""Centralized shadcn/ui Zinc Dark theme tokens, DPI/titlebar helpers, and ttk.Style setup."""

import ctypes
from dataclasses import dataclass
import sys
import tkinter as tk
from tkinter import ttk


def enable_high_dpi_awareness() -> None:
    """Enable crisp High-DPI rendering on Windows before creating Tk root."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def apply_dark_titlebar(window: tk.Misc) -> None:
    """Request Windows 10/11 immersive dark title bar for a Tk or Toplevel window."""
    if sys.platform != "win32":
        return
    try:
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id()) or window.winfo_id()
        value = ctypes.c_int(1)
        # DWMWA_USE_IMMUTABLE_DARK_MODE = 20 (Win 11 / Win 10 2004+), fallback 19
        for attr in (20, 19):
            res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attr, ctypes.byref(value), ctypes.sizeof(value)
            )
            if res == 0:
                break
    except Exception:
        pass


@dataclass(frozen=True)
class AppColors:
    """Immutable semantic color palette inspired by shadcn/ui Zinc Dark."""

    # Canvas & Surfaces
    background: str = "#09090B"          # zinc-950 workspace canvas
    surface: str = "#18181B"             # zinc-900 card / table / input surface
    surface_elevated: str = "#1F1F23"    # subtle elevated header / popover
    surface_muted: str = "#27272A"       # zinc-800 pill track / secondary / hover
    surface_hover: str = "#27272A"       # zinc-800 subtle hover
    surface_active: str = "#3F3F46"      # zinc-700 selected row / active press

    # Sidebar
    sidebar_bg: str = "#09090B"          # zinc-950
    sidebar_border: str = "#27272A"      # zinc-800
    sidebar_item_hover: str = "#18181B"  # zinc-900
    sidebar_item_active: str = "#FAFAFA" # zinc-50 crisp active pill
    sidebar_item_active_fg: str = "#09090B"

    # Borders & Focus Rings
    border: str = "#27272A"              # zinc-800 hairline border
    input_border: str = "#3F3F46"        # zinc-700 form control border
    ring: str = "#FAFAFA"                # zinc-50 focus outline
    divider: str = "#27272A"

    # Primary (shadcn dark high-contrast zinc-50)
    primary: str = "#FAFAFA"
    primary_hover: str = "#E4E4E7"       # zinc-200
    primary_pressed: str = "#D4D4D8"     # zinc-300
    primary_foreground: str = "#09090B"  # zinc-950
    primary_subtle: str = "#27272A"

    # Secondary (muted zinc-800)
    secondary: str = "#27272A"
    secondary_hover: str = "#3F3F46"     # zinc-700
    secondary_foreground: str = "#FAFAFA"

    # Typography
    text_primary: str = "#FAFAFA"        # zinc-50
    text_secondary: str = "#D4D4D8"      # zinc-300
    text_muted: str = "#A1A1AA"          # zinc-400
    text_on_primary: str = "#09090B"

    # Semantic Status (shadcn dark translucent-style badges)
    success: str = "#22C55E"
    success_bg: str = "#052E16"
    success_border: str = "#166534"
    success_text: str = "#4ADE80"

    warning: str = "#F59E0B"
    warning_bg: str = "#2A1B05"
    warning_border: str = "#92400E"
    warning_text: str = "#FBBF24"

    danger: str = "#EF4444"
    danger_hover: str = "#DC2626"
    danger_pressed: str = "#B91C1C"
    danger_bg: str = "#2A0B0E"
    danger_border: str = "#991B1B"
    danger_text: str = "#F87171"
    danger_foreground: str = "#FAFAFA"

    info: str = "#A1A1AA"
    info_bg: str = "#27272A"
    info_border: str = "#3F3F46"
    info_text: str = "#E4E4E7"


@dataclass(frozen=True)
class AppTypography:
    """Centralized typography scale."""

    family: str = "Segoe UI"
    mono_family: str = "Consolas"
    h1: tuple = ("Segoe UI", 18, "bold")
    h2: tuple = ("Segoe UI", 14, "bold")
    h3: tuple = ("Segoe UI", 11, "bold")
    body: tuple = ("Segoe UI", 10)
    body_bold: tuple = ("Segoe UI", 10, "bold")
    field_label: tuple = ("Segoe UI", 9, "bold")
    sidebar_section: tuple = ("Segoe UI", 8, "bold")
    caption: tuple = ("Segoe UI", 9)
    button: tuple = ("Segoe UI", 10, "bold")
    chip: tuple = ("Segoe UI", 9, "bold")
    stat_value: tuple = ("Segoe UI", 20, "bold")
    mono: tuple = ("Consolas", 10)


@dataclass(frozen=True)
class AppSpacing:
    """Consistent spacing and layout metrics."""

    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24
    sidebar_width: int = 236
    topbar_height: int = 64
    table_row_height: int = 38


@dataclass(frozen=True)
class AppRadius:
    """Border radii for rounded shadcn/ui Zinc Dark surfaces and pills."""

    control: int = 8
    card: int = 12
    pill: int = 14


class AppTheme:
    """Configures root window and ttk styles from centralized dark design tokens."""

    colors = AppColors()
    typography = AppTypography()
    spacing = AppSpacing()
    radius = AppRadius()

    @classmethod
    def apply(cls, root: tk.Misc) -> ttk.Style:
        """Apply the shadcn/ui Zinc Dark theme to the Tk root and ttk widgets."""
        c = cls.colors
        root.configure(bg=c.background)
        apply_dark_titlebar(root)

        # Style Combobox dropdown popdown listboxes without touching label fonts
        root.option_add("*TCombobox*Listbox.background", c.surface)
        root.option_add("*TCombobox*Listbox.foreground", c.text_primary)
        root.option_add("*TCombobox*Listbox.selectBackground", c.surface_active)
        root.option_add("*TCombobox*Listbox.selectForeground", c.text_primary)

        style = ttk.Style(root)
        style.theme_use("clam")

        cls._configure_containers_and_labels(style)
        cls._configure_inputs(style)
        cls._configure_buttons(style)
        cls._configure_treeview_and_scrollbars(style)
        return style

    @classmethod
    def _configure_containers_and_labels(cls, style: ttk.Style) -> None:
        c = cls.colors
        t = cls.typography

        style.configure("TFrame", background=c.background)
        style.configure("Surface.TFrame", background=c.surface)
        style.configure("Muted.TFrame", background=c.surface_muted)
        style.configure("Sidebar.TFrame", background=c.sidebar_bg)

        style.configure(
            "TLabel",
            background=c.background,
            foreground=c.text_primary,
            font=t.body,
        )
        style.configure(
            "Surface.TLabel",
            background=c.surface,
            foreground=c.text_primary,
            font=t.body,
        )
        style.configure(
            "Title.TLabel",
            background=c.background,
            foreground=c.text_primary,
            font=t.h1,
        )
        style.configure(
            "TopbarTitle.TLabel",
            background=c.background,
            foreground=c.text_primary,
            font=t.h2,
        )
        style.configure(
            "Subtitle.TLabel",
            background=c.background,
            foreground=c.text_muted,
            font=t.body,
        )
        style.configure(
            "Section.TLabel",
            background=c.surface,
            foreground=c.text_primary,
            font=t.h3,
        )
        style.configure(
            "FieldLabel.TLabel",
            background=c.surface,
            foreground=c.text_secondary,
            font=t.field_label,
        )
        style.configure(
            "Muted.TLabel",
            background=c.background,
            foreground=c.text_muted,
            font=t.caption,
        )
        style.configure(
            "SurfaceMuted.TLabel",
            background=c.surface,
            foreground=c.text_muted,
            font=t.caption,
        )
        style.configure(
            "Error.TLabel",
            background=c.surface,
            foreground=c.danger_text,
            font=t.caption,
        )
        style.configure(
            "StatusOk.TLabel",
            background=c.sidebar_bg,
            foreground=c.success_text,
            font=t.caption,
        )
        style.configure("TSeparator", background=c.divider)

    @classmethod
    def _configure_inputs(cls, style: ttk.Style) -> None:
        c = cls.colors
        t = cls.typography

        style.configure(
            "TEntry",
            fieldbackground=c.surface,
            foreground=c.text_primary,
            bordercolor=c.input_border,
            lightcolor=c.input_border,
            darkcolor=c.input_border,
            insertcolor=c.text_primary,
            padding=(8, 6),
            font=t.body,
        )
        style.map(
            "TEntry",
            bordercolor=[("focus", c.ring), ("readonly", c.border)],
            fieldbackground=[("readonly", c.surface_muted), ("disabled", c.surface_muted)],
            foreground=[("readonly", c.text_muted), ("disabled", c.text_muted)],
        )

        # Borderless inner entry inside rounded Canvas AppTextField
        style.configure(
            "Flat.TEntry",
            fieldbackground=c.surface,
            foreground=c.text_primary,
            borderwidth=0,
            relief="flat",
            insertcolor=c.text_primary,
            selectbackground=c.surface_active,
            selectforeground=c.text_primary,
            padding=(2, 3),
            font=t.body,
        )
        style.map(
            "Flat.TEntry",
            fieldbackground=[("readonly", c.surface_muted), ("disabled", c.surface_muted)],
            foreground=[("readonly", c.text_muted), ("disabled", c.text_muted)],
        )

        # Borderless inner combobox inside rounded Canvas AppDropdown
        style.configure(
            "Flat.TCombobox",
            fieldbackground=c.surface,
            background=c.surface,
            foreground=c.text_primary,
            borderwidth=0,
            lightcolor=c.surface,
            darkcolor=c.surface,
            bordercolor=c.surface,
            arrowcolor=c.text_muted,
            insertcolor=c.text_primary,
            relief="flat",
            padding=(2, 2),
            font=t.body,
        )
        style.map(
            "Flat.TCombobox",
            fieldbackground=[("readonly", c.surface), ("disabled", c.surface_muted)],
            foreground=[("readonly", c.text_primary), ("disabled", c.text_muted)],
            bordercolor=[("focus", c.surface), ("readonly", c.surface)],
            lightcolor=[("focus", c.surface), ("readonly", c.surface)],
            darkcolor=[("focus", c.surface), ("readonly", c.surface)],
            selectbackground=[("readonly", c.surface)],
            selectforeground=[("readonly", c.text_primary)],
        )

        style.configure(
            "TCombobox",
            fieldbackground=c.surface,
            background=c.surface_muted,
            foreground=c.text_primary,
            bordercolor=c.input_border,
            arrowcolor=c.text_muted,
            padding=(8, 5),
            font=t.body,
        )

        style.configure(
            "TSpinbox",
            fieldbackground=c.surface,
            background=c.surface_muted,
            foreground=c.text_primary,
            bordercolor=c.input_border,
            arrowcolor=c.text_muted,
            insertcolor=c.text_primary,
            padding=(6, 4),
            font=t.body,
        )

    @classmethod
    def _configure_buttons(cls, style: ttk.Style) -> None:
        c = cls.colors
        t = cls.typography
        base = {"font": t.button, "padding": (14, 7), "borderwidth": 1, "relief": "flat"}

        style.configure(
            "Primary.TButton",
            **base,
            background=c.primary,
            foreground=c.primary_foreground,
            bordercolor=c.primary,
        )
        style.configure(
            "Outline.TButton",
            **base,
            background=c.surface,
            foreground=c.text_primary,
            bordercolor=c.input_border,
        )
        style.configure(
            "Secondary.TButton",
            **base,
            background=c.secondary,
            foreground=c.secondary_foreground,
            bordercolor=c.border,
        )
        style.configure(
            "Danger.TButton",
            **base,
            background=c.danger,
            foreground=c.danger_foreground,
            bordercolor=c.danger,
        )
        style.configure(
            "Ghost.TButton",
            font=t.button,
            padding=(10, 6),
            borderwidth=0,
            relief="flat",
            background=c.surface,
            foreground=c.text_muted,
        )

    @classmethod
    def _configure_treeview_and_scrollbars(cls, style: ttk.Style) -> None:
        c = cls.colors
        t = cls.typography

        style.configure(
            "Treeview",
            background=c.surface,
            fieldbackground=c.surface,
            foreground=c.text_primary,
            borderwidth=0,
            relief="flat",
            rowheight=cls.spacing.table_row_height,
            font=t.body,
        )
        style.map(
            "Treeview",
            background=[("selected", c.surface_muted)],
            foreground=[("selected", c.text_primary)],
        )
        style.configure(
            "Treeview.Heading",
            background=c.surface,
            foreground=c.text_muted,
            bordercolor=c.border,
            borderwidth=0,
            relief="flat",
            padding=(10, 8),
            font=t.field_label,
        )
        style.map(
            "Treeview.Heading",
            background=[("active", c.surface_muted)],
            foreground=[("active", c.text_primary)],
        )

        style.configure(
            "TScrollbar",
            background=c.surface_muted,
            troughcolor=c.surface,
            bordercolor=c.surface,
            arrowcolor=c.text_muted,
            relief="flat",
            width=10,
        )
        style.map(
            "TScrollbar",
            background=[("active", c.surface_active)],
        )
