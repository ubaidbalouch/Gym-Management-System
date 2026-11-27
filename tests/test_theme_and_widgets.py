"""Unit tests for AppTheme typography/styles and reusable rounded widgets."""

import tkinter as tk
from tkinter import font as tkfont
import unittest

from src.common.theme import AppTheme
from src.common.widgets import (
    AppButton,
    AppCard,
    AppChip,
    AppChipGroup,
    AppDateField,
    AppDropdown,
    AppSidebar,
    AppTable,
    AppTextField,
    SidebarNavItem,
    StatCard,
    StatusChip,
    TableColumn,
    status_row_tag,
)


class TestThemeAndWidgets(unittest.TestCase):
    def setUp(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.style = AppTheme.apply(self.root)

    def tearDown(self) -> None:
        self.root.destroy()

    def test_theme_styles_and_typography_configured(self) -> None:
        self.assertEqual(self.root.cget("bg"), AppTheme.colors.background)
        self.assertEqual(AppTheme.colors.background, "#09090B")
        self.assertEqual(AppTheme.colors.surface, "#18181B")
        title_font = tkfont.Font(font=self.style.lookup("Title.TLabel", "font")).actual()
        topbar_font = tkfont.Font(font=self.style.lookup("TopbarTitle.TLabel", "font")).actual()
        section_font = tkfont.Font(font=self.style.lookup("Section.TLabel", "font")).actual()
        self.assertEqual((title_font["size"], title_font["weight"]), (18, "bold"))
        self.assertEqual((topbar_font["size"], topbar_font["weight"]), (14, "bold"))
        self.assertEqual((section_font["size"], section_font["weight"]), (11, "bold"))
        for style_name in (
            "Primary.TButton",
            "Outline.TButton",
            "Secondary.TButton",
            "Danger.TButton",
            "Ghost.TButton",
            "Flat.TEntry",
            "Flat.TCombobox",
            "Treeview",
        ):
            self.assertIsNotNone(self.style.configure(style_name))

    def test_text_field_and_readonly_behavior(self) -> None:
        field = AppTextField(self.root, label="Name", placeholder="Enter name")
        self.assertEqual(field.get(), "")
        field.set("Hamza")
        self.assertEqual(field.get(), "Hamza")
        field.set_error("Required")
        self.assertEqual(field.error_var.get(), "Required")
        field.clear()
        self.assertEqual(field.get(), "")
        self.assertEqual(field.error_var.get(), "")

        ro = AppTextField(self.root, label="ID", readonly=True)
        ro.set(42)
        self.assertEqual(ro.get(), "42")
        self.assertEqual(str(ro.entry.cget("state")), "readonly")

    def test_dropdown_chip_card_sidebar_table_and_date_field(self) -> None:
        dropdown = AppDropdown(self.root, label="Type", options=("Monthly", "Admission"))
        dropdown.set_options(("Monthly", "Admission", "Personal Training"))
        dropdown.pack(fill="x")
        self.root.update_idletasks()
        dropdown._toggle_sheet()
        self.root.after(120, self.root.quit)
        self.root.mainloop()
        self.assertIsNotNone(dropdown._sheet)
        self.assertTrue(dropdown._sheet.winfo_exists())
        dropdown._sheet._pick("Admission")
        self.assertEqual(dropdown.get(), "Admission")
        dropdown.set("Monthly")
        self.assertEqual(dropdown.get(), "Monthly")
        dropdown.set_error("Required")
        self.assertEqual(dropdown.error_var.get(), "Required")
        dropdown.clear()
        self.assertEqual(dropdown.get(), "")
        self.assertEqual(dropdown.error_var.get(), "")

        selected_keys: list[str] = []
        chips = AppChipGroup(
            self.root,
            options=(("All", "All"), ("Paid", "Paid")),
            initial_key="All",
            on_change=selected_keys.append,
        )
        self.assertEqual(chips.get_selected(), "All")
        chips.select("Paid")
        self.assertEqual(chips.get_selected(), "Paid")
        self.assertEqual(selected_keys, ["Paid"])

        chip = AppChip(self.root, "Tag", variant="primary")
        self.assertEqual(chip.cget("text"), "Tag")

        status_chip = StatusChip(self.root, "Pending")
        status_chip.set_status("Paid")
        self.assertEqual(status_chip.cget("text"), "Paid")

        card = AppCard(self.root, title="Section")
        card.pack(fill="x")
        field_in_card = AppTextField(card.content, label="Name")
        field_in_card.pack(fill="x")
        self.root.update_idletasks()
        base_height = int(float(card["height"]))
        field_in_card.set_error("Name is required.")
        self.root.update_idletasks()
        self.assertGreater(int(float(card["height"])), base_height)

        stat = StatCard(card.content, "Members", "5", badge_text="Active")
        stat.set_value("10")
        self.assertEqual(stat.value_var.get(), "10")

        clicked: list[str] = []
        btn_primary = AppButton(
            self.root, text="Save", variant="primary", pill=True, command=lambda: clicked.append("save")
        )
        btn_outline = AppButton(self.root, text="Cancel", variant="outline")
        self.assertEqual(btn_primary.cget("text"), "Save")
        self.assertEqual(btn_outline.cget("text"), "Cancel")
        btn_primary.invoke()
        self.assertEqual(clicked, ["save"])

        nav_hits: list[str] = []
        sidebar = AppSidebar(
            self.root,
            items=(
                SidebarNavItem("dashboard", "Dashboard", "▣", "Overview"),
                SidebarNavItem("members", "Members", "◎", "Operations"),
            ),
            on_select=nav_hits.append,
        )
        sidebar.select("members")
        self.assertEqual(sidebar.get_selected(), "members")
        self.assertEqual(nav_hits, ["members"])

        table = AppTable(
            self.root,
            columns=(TableColumn("id", "ID", 60), TableColumn("status", "Status", 80)),
        )
        table.set_rows([(1, "Paid"), (2, "Partial")], tag_fn=lambda r, i: status_row_tag(r[1], i))
        self.assertEqual(len(table.tree.get_children()), 2)

        date_field = AppDateField(self.root)
        date_field.set("27-11-2026")
        self.assertEqual(date_field.get_iso(), "2026-11-27")
        self.assertTrue(date_field.is_valid_or_empty())


if __name__ == "__main__":
    unittest.main()
