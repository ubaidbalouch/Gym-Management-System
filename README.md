# Gym Management System (GymOS)

A desktop **Gym Management Software** built with **Python**, **Tkinter**, and **SQLite**, organized with a **feature-first architecture** and a centralized **shadcn/ui Zinc Dark** design system (`PKR` currency).

---

## Features

- **Dashboard**: Real-time KPI cards (total members, pending/partial fee count, total billed, collected, and outstanding PKR balances), status summary pills, payment breakdown table, and Excel report export.
- **Member Management**: Register, update, inspect, and delete members with cascading cleanup of assigned fees and payment records, plus a detailed member profile & fee breakdown dialog.
- **Member Fees**: View all assigned fees with segmented status pill filters (`All`, `Paid`, `Partial`, `Pending`) and Excel export.
- **Payments (PKR)**: Assign fee categories (`Monthly Fee`, `Admission Fee`, `Personal Training`, `Supplement Fee`) and record partial or full payments via `Cash`, `Card`, `Bank Transfer`, `Jazz Cash`, or `Easy Paisa` with automatic status transitions (`Pending` → `Partial` → `Paid`).
- **Payment History**: Chronological fee and payment ledger across all members with status filtering.
- **Search & Reports**: Search members by Member ID, name, or phone, inspect comprehensive fee summaries, and export individual member reports to `.xlsx`.
- **Help & Guide**: Built-in 2×2 quick-reference card guide.

---

## Project Structure

```text
Gym-Management-System/
├── app.py                              # Thin executable entry point
├── Gym Management System.spec          # PyInstaller build specification
├── requirements.txt                    # Optional Excel export dependencies (pandas, openpyxl)
├── gym.db                              # Local SQLite database
├── logo.ico                            # Application icon
├── tests/                              # Automated unit & integration tests (unittest)
│   ├── test_repositories.py
│   ├── test_theme_and_widgets.py
│   └── test_app_navigation.py
└── src/
    ├── main.py                         # GymManagementApp sidebar shell & route coordinator
    ├── common/                         # Shared foundation used across all features
    │   ├── theme/
    │   │   └── app_theme.py            # AppColors, AppTypography, AppSpacing, AppRadius, AppTheme
    │   ├── widgets/                    # Reusable rounded Canvas/ttk UI components
    │   │   ├── app_button.py           # AppButton (primary, outline, secondary, danger, ghost + pill)
    │   │   ├── app_card.py             # AppCard & StatCard
    │   │   ├── app_chip.py             # AppChip, StatusChip & AppChipGroup
    │   │   ├── app_date_picker.py      # AppDateField & AppDatePickerDialog
    │   │   ├── app_dialogs.py          # AppModalDialog & message/file helpers
    │   │   ├── app_dropdown.py         # AppDropdown with rounded dark popover sheet
    │   │   ├── app_sidebar.py          # AppSidebar left navigation rail
    │   │   ├── app_table.py            # AppTable & status_row_tag
    │   │   ├── app_text_field.py       # AppTextField with focus ring & inline validation
    │   │   └── canvas_primitives.py    # Exact-arc rounded rectangle & pill primitives
    │   ├── database/
    │   │   ├── db_connection.py        # DatabaseConnection (context manager, FK pragma, PyInstaller path)
    │   │   └── migrations.py           # Idempotent schema creation & default fee_types seeding
    │   └── utils/
    │       ├── currency.py             # format_pkr(), parse_positive_amount()
    │       ├── dates.py                # parse_ddmmyyyy_to_iso(), format_display_date()
    │       └── excel_exporter.py       # Safe pandas/openpyxl Excel export helper
    └── features/                       # Feature-first vertical slices
        ├── dashboard/                  # dashboard_repository.py, dashboard_view.py
        ├── members/                    # member_model.py, member_repository.py, member_management_view.py, member_details_dialog.py
        ├── fees/                       # fee_model.py, fee_repository.py, member_fees_view.py
        ├── payments/                   # payment_model.py, payment_repository.py, payment_management_view.py, payment_history_view.py
        ├── search/                     # search_repository.py, search_view.py
        └── help/                       # help_view.py
```

---

## Getting Started

### Prerequisites
- **Python 3.12+** (standard library `tkinter` and `sqlite3` included)
- Optional for Excel (`.xlsx`) exports:
  ```powershell
  python -m pip install -r requirements.txt
  ```

### Run the Application
```powershell
python app.py
```

### Run Automated Tests
```powershell
python -m compileall -q app.py src tests
python -m unittest discover -s tests -v
```

### Build Windows Executable (Optional)
```powershell
pyinstaller "Gym Management System.spec"
```
