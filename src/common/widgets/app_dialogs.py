"""Modal dialog base class with dark title bar and standard message/file wrappers."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from src.common.theme import AppTheme, apply_dark_titlebar


class AppModalDialog(tk.Toplevel):
    """Themed dark modal dialog centered over its parent window."""

    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        resizable: bool = True,
    ) -> None:
        super().__init__(parent)
        self.title(title)
        self.configure(bg=AppTheme.colors.background)
        self.resizable(resizable, resizable)
        self.transient(parent.winfo_toplevel())
        apply_dark_titlebar(self)

        if width and height:
            self.geometry(f"{width}x{height}")

        self.body = ttk.Frame(self, padding=AppTheme.spacing.lg)
        self.body.pack(fill="both", expand=True)

    def show_modal(self) -> None:
        """Center relative to parent and grab modal focus."""
        self.update_idletasks()
        apply_dark_titlebar(self)
        parent = self.master.winfo_toplevel()
        px = parent.winfo_rootx() + max(0, (parent.winfo_width() - self.winfo_width()) // 2)
        py = parent.winfo_rooty() + max(0, (parent.winfo_height() - self.winfo_height()) // 2)
        self.geometry(f"+{px}+{py}")
        self.grab_set()
        self.focus_set()


def show_info(title: str, message: str, parent: Optional[tk.Misc] = None) -> None:
    messagebox.showinfo(title, message, parent=parent)


def show_warning(title: str, message: str, parent: Optional[tk.Misc] = None) -> None:
    messagebox.showwarning(title, message, parent=parent)


def show_error(title: str, message: str, parent: Optional[tk.Misc] = None) -> None:
    messagebox.showerror(title, message, parent=parent)


def ask_confirm(
    title: str,
    message: str,
    icon: str = "question",
    parent: Optional[tk.Misc] = None,
) -> bool:
    return bool(messagebox.askyesno(title, message, icon=icon, parent=parent))


def ask_save_excel(initial_filename: str = "", parent: Optional[tk.Misc] = None) -> str:
    return filedialog.asksaveasfilename(
        parent=parent,
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        initialfile=initial_filename,
    )
