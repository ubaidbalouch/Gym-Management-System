import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional
from database import GymDatabase


class MemberManagementFrame(ttk.Frame):
    def __init__(self, parent, database: GymDatabase, fees_frame=None):
        super().__init__(parent)
        self.database = database
        self.fees_frame = fees_frame
        self.setup_ui()
        self.refresh_members_list()
   
    def setup_ui(self):
        # Title
        title_label = ttk.Label(self, text="Member Management", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
       
        # Input Frame
        input_frame = ttk.LabelFrame(self, text="Add/Edit Member", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)
       
        # Member ID (for editing)
        ttk.Label(input_frame, text="Member ID:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.member_id_var = tk.StringVar()
        self.member_id_entry = ttk.Entry(input_frame, textvariable=self.member_id_var, state="readonly")
        self.member_id_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
       
        # Name
        ttk.Label(input_frame, text="Name:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(input_frame, textvariable=self.name_var, width=30)
        self.name_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
       
        # Phone
        ttk.Label(input_frame, text="Phone:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.phone_var = tk.StringVar()
        self.phone_entry = ttk.Entry(input_frame, textvariable=self.phone_var, width=20)
        self.phone_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
       
        # Buttons Frame
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
       
        ttk.Button(button_frame, text="Add Member", command=self.add_member).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Update Member", command=self.update_member).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Clear All Data", command=self.clear_form).pack(side="left", padx=5)
       
        # Members List
        list_frame = ttk.LabelFrame(self, text="Members List", padding=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
       
        # Treeview for members
        columns = ("ID", "Name", "Phone")
        self.members_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
       
        for col in columns:
            self.members_tree.heading(col, text=col)
            self.members_tree.column(col, width=100)
       
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.members_tree.yview)
        self.members_tree.configure(yscrollcommand=scrollbar.set)
       
        self.members_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
       
        # Bind double-click event (open details window)
        self.members_tree.bind("<Double-1>", self.open_selected_details)
       
        # Action buttons for selected member
        action_frame = ttk.Frame(list_frame)
        action_frame.pack(fill="x", pady=5)
       
        ttk.Button(action_frame, text="View Details", command=self.open_selected_details).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Edit Selected", command=self.edit_selected).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=5)
       
        # Configure grid weights
        input_frame.columnconfigure(1, weight=1)
   
    def reset_form_fields(self):
        """Clear form fields only (used after add/update/delete operations)"""
        try:
            # Clear all input fields
            self.member_id_var.set("")
            self.name_var.set("")
            self.phone_var.set("")
           
            # Reset member ID entry to readonly state
            self.member_id_entry.config(state="normal")
            self.member_id_entry.delete(0, "end")
            self.member_id_entry.config(state="readonly")
           
            # Clear selection in members tree
            for item in self.members_tree.selection():
                self.members_tree.selection_remove(item)
           
            # Focus on name field for next entry
            self.name_entry.focus_set()
        except Exception as e:
            print(f"Error resetting form: {e}")
   
    def clear_form(self):
        """Clear all members data - Delete all members, fees, and payments"""
        try:
            # Get count of members
            members = self.database.get_all_members()
            member_count = len(members)
           
            if member_count == 0:
                messagebox.showinfo("Info", "No members to delete. Database is already empty.")
                return
           
            # Confirmation dialog
            confirm_msg = f"⚠️ WARNING: This will delete ALL members data!\n\n"
            confirm_msg += f"• {member_count} member(s) will be deleted\n"
            confirm_msg += f"• All fees and payments will be deleted\n"
            confirm_msg += f"• This action CANNOT be undone!\n\n"
            confirm_msg += f"Are you sure you want to continue?"
           
            if not messagebox.askyesno("Confirm Delete All", confirm_msg, icon='warning'):
                return
           
            # Double confirmation
            if not messagebox.askyesno("Final Confirmation",
                                      "⚠️ LAST WARNING!\n\n"
                                      "You are about to DELETE ALL DATA!\n\n"
                                      "This will permanently remove:\n"
                                      "• All members\n"
                                      "• All fees\n"
                                      "• All payment records\n\n"
                                      "Click YES to proceed or NO to cancel.",
                                      icon='error'):
                return
           
            # Delete all members and related data
            success = self.database.delete_all_members()
           
            if success:
                # Clear form fields
                self.reset_form_fields()
               
                # Refresh lists
                self.refresh_members_list()
                if self.fees_frame:
                    self.fees_frame.refresh_fees_list()
               
                messagebox.showinfo("Success", f"All members data has been deleted successfully!\n\n{member_count} member(s) removed.")
            else:
                messagebox.showerror("Error", "Failed to delete all members data!")
               
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear all data:\n{str(e)}")
            import traceback
            print(traceback.format_exc())
   
    def add_member(self):
        """Add a new member"""
        if not self.name_var.get().strip():
            messagebox.showerror("Error", "Name is required!")
            return
       
        member_id = self.database.add_member(
            self.name_var.get().strip(),
            self.phone_var.get().strip()
        )
       
        if member_id:
            self.reset_form_fields()
            self.refresh_members_list()
            if self.fees_frame:
                self.fees_frame.refresh_fees_list()
        else:
            messagebox.showerror("Error", "Failed to add member!")
   
    def update_member(self):
        """Update existing member"""
        if not self.member_id_var.get():
            messagebox.showerror("Error", "Please select a member to update!")
            return
       
        try:
            member_id = int(self.member_id_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid member ID!")
            return
       
        success = self.database.update_member(
            member_id,
            self.name_var.get().strip(),
            self.phone_var.get().strip()
        )
       
        if success:
            self.reset_form_fields()
            self.refresh_members_list()
            if self.fees_frame:
                self.fees_frame.refresh_fees_list()
        else:
            messagebox.showerror("Error", "Failed to update member!")
   
    def edit_selected(self):
        """Edit the selected member"""
        selection = self.members_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a member to edit!")
            return
       
        item = self.members_tree.item(selection[0])
        values = item['values']
        self.member_id_var.set(values[0])
        self.name_var.set(values[1])
        self.phone_var.set(values[2])
        self.member_id_entry.config(state="normal")
   
    def delete_selected(self):
        """Delete the selected member"""
        selection = self.members_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a member to delete!")
            return
       
        item = self.members_tree.item(selection[0])
        member_id = item['values'][0]
        member_name = item['values'][1]
       
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {member_name}?"):
            success = self.database.delete_member(member_id)
            if success:
                self.reset_form_fields()
                self.refresh_members_list()
                if self.fees_frame:
                    self.fees_frame.refresh_fees_list()
            else:
                messagebox.showerror("Error", "Failed to delete member!")
   
    def on_member_select(self, event):
        self.edit_selected()


    def open_selected_details(self, event=None):
        try:
            selection = self.members_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a member!")
                return
            item = self.members_tree.item(selection[0])
            if not item['values']:
                messagebox.showerror("Error", "Invalid member selection!")
                return
            member_id = item['values'][0]
            member = self.database.get_member_by_id(member_id)
            if not member:
                messagebox.showerror("Error", f"Member ID {member_id} not found in database!")
                return


            detail_win = tk.Toplevel(self)
            detail_win.title(f"Member Details - {member.get('name', 'Unknown')}")
            detail_win.geometry("700x500")


            header = ttk.Label(detail_win, text=f"Member Details", font=("Arial", 14, "bold"))
            header.pack(pady=8)


            info_frame = ttk.Frame(detail_win)
            info_frame.pack(fill="x", padx=10)


            ttk.Label(info_frame, text=f"Member ID: {member['member_id']}").grid(row=0, column=0, sticky="w", padx=4, pady=2)
            ttk.Label(info_frame, text=f"Name: {member['name']}").grid(row=0, column=1, sticky="w", padx=4, pady=2)
            ttk.Label(info_frame, text=f"Phone: {member['phone'] or ''}").grid(row=1, column=0, sticky="w", padx=4, pady=2)
            ttk.Label(info_frame, text=f"Registration: {(member['registration_date'] or '')[:10] if member.get('registration_date') else ''}").grid(row=1, column=1, sticky="w", padx=4, pady=2)


            fees_frame = ttk.LabelFrame(detail_win, text="Fees & Status", padding=6)
            fees_frame.pack(fill="both", expand=True, padx=10, pady=8)


            fees_cols = ("Fee ID", "Type", "Total", "Paid", "Pending", "Status", "Payment Method", "Assign Date")
            fees_tree = ttk.Treeview(fees_frame, columns=fees_cols, show="headings", height=12)
            for c in fees_cols:
                fees_tree.heading(c, text=c)
                fees_tree.column(c, width=95)
            fees_scrollbar = ttk.Scrollbar(fees_frame, orient="vertical", command=fees_tree.yview)
            fees_tree.configure(yscrollcommand=fees_scrollbar.set)
            fees_tree.pack(side="left", fill="both", expand=True)
            fees_scrollbar.pack(side="right", fill="y")


            try:
                # Ensure member_id is int
                member_id = int(member['member_id']) if member.get('member_id') else None
                if not member_id:
                    fees_tree.insert("", "end", values=("Invalid member ID", "", "", "", "", "", "", ""))
                    return
               
                fees = self.database.get_member_fees(member_id)
               
                if fees:
                    for f in fees:
                        total = f.get('total_amount') if f.get('total_amount') is not None else 0.0
                        paid = f.get('paid_amount') if f.get('paid_amount') is not None else 0.0
                        pending = total - paid
                        fees_tree.insert("", "end", values=(
                            f.get('fee_id', ''),
                            f.get('fee_name', ''),
                            f"PKR {total:.2f}",
                            f"PKR {paid:.2f}",
                            f"PKR {pending:.2f}",
                            f.get('payment_status') or 'Pending',
                            f.get('last_payment_method') or 'N/A',
                            (f.get('created_date') or '')[:10] if f.get('created_date') else ''
                        ))
                else:
                    fees_tree.insert("", "end", values=("No fees assigned", "", "", "", "", "", "", ""))
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid member ID: {str(e)}")
                fees_tree.insert("", "end", values=("Error: Invalid member ID", "", "", "", "", "", "", ""))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load fees: {str(e)}")
                import traceback
                traceback.print_exc()
                fees_tree.insert("", "end", values=("Error loading fees", "", "", "", "", "", "", ""))


            actions = ttk.Frame(detail_win)
            actions.pack(fill="x", padx=10, pady=6)


            def export_excel():
                filename = filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                    initialfile=f"member_{member['member_id']}_details.xlsx"
                )
                if filename:
                    ok = self.database.export_member_details_to_excel(member['member_id'], filename)
                    if ok:
                        messagebox.showinfo("Success", f"Saved: {filename}")
                    else:
                        messagebox.showerror("Error", f"Failed to export Excel.")


            ttk.Button(actions, text="Download Excel", command=export_excel).pack(side="right")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open member details:\n{str(e)}")
            import traceback
            print(traceback.format_exc())
   
    def refresh_members_list(self):
        for item in self.members_tree.get_children():
            self.members_tree.delete(item)
        members = self.database.get_all_members()
        for member in members:
            self.members_tree.insert("", "end", values=(
                member['member_id'],
                member['name'],
                member['phone'] or ""
            ))


class PaymentManagementFrame(ttk.Frame):
    def __init__(self, parent, database: GymDatabase, fees_frame=None, dashboard_frame=None):
        super().__init__(parent)
        self.database = database
        self.fees_frame = fees_frame
        self.dashboard_frame = dashboard_frame
        self.setup_ui()
   
    def parse_ddmmyyyy_to_iso(self, date_text: str) -> str:
        try:
            parts = date_text.split('-')
            if len(parts) != 3: return None
            dd, mm, yyyy = parts
            day, month, year = int(dd), int(mm), int(yyyy)
            import datetime as _dt
            _dt.date(year, month, day)
            return f"{year:04d}-{month:02d}-{day:02d}"
        except Exception: return None
   
    def open_date_picker(self, target_var: tk.StringVar):
        top = tk.Toplevel(self)
        top.title("Select Date")
        container = ttk.Frame(top, padding=8)
        container.pack()
        ttk.Label(container, text="Day").grid(row=0, column=0)
        day_var = tk.StringVar(value="01")
        ttk.Spinbox(container, from_=1, to=31, textvariable=day_var, width=4).grid(row=0, column=1)
        ttk.Label(container, text="Month").grid(row=1, column=0)
        month_var = tk.StringVar(value="01")
        ttk.Spinbox(container, from_=1, to=12, textvariable=month_var, width=4).grid(row=1, column=1)
        ttk.Label(container, text="Year").grid(row=2, column=0)
        import datetime as _dt
        year_var = tk.StringVar(value=str(_dt.date.today().year))
        ttk.Spinbox(container, from_=1900, to=2100, textvariable=year_var, width=6).grid(row=2, column=1)
        def set_date():
            target_var.set(f"{int(day_var.get()):02d}-{int(month_var.get()):02d}-{int(year_var.get()):04d}")
            top.destroy()
        ttk.Button(container, text="OK", command=set_date).grid(row=3, column=0, columnspan=2, pady=6)
   
    def setup_ui(self):
        ttk.Label(self, text="Payment Management", font=("Arial", 16, "bold")).pack(pady=10)
        fee_frame = ttk.LabelFrame(self, text="Assign Fee to Member", padding=6)
        fee_frame.pack(fill="x", padx=10, pady=2)
        ttk.Label(fee_frame, text="Member:").grid(row=0, column=0, sticky="w", padx=4)
        self.member_var = tk.StringVar()
        self.member_combo = ttk.Combobox(
            fee_frame,
            textvariable=self.member_var,
            width=28,
            state="readonly",
            postcommand=self.populate_members_dropdown,
        )
        self.member_combo.grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Label(fee_frame, text="Fee Type:").grid(row=1, column=0, sticky="w", padx=4)
        self.fee_type_var = tk.StringVar()
        self.fee_type_combo = ttk.Combobox(fee_frame, textvariable=self.fee_type_var, width=28, state="readonly")
        self.fee_type_combo.grid(row=1, column=1, sticky="ew", padx=4)
        ttk.Label(fee_frame, text="Amount:").grid(row=2, column=0, sticky="w", padx=4)
        self.amount_var = tk.StringVar()
        ttk.Entry(fee_frame, textvariable=self.amount_var, width=16).grid(row=2, column=1, sticky="w", padx=4)
        ttk.Label(fee_frame, text="Assigned Date (DD-MM-YYYY):").grid(row=3, column=0, sticky="w", padx=4)
        self.assigned_date_var = tk.StringVar()
        dw = ttk.Frame(fee_frame); dw.grid(row=3, column=1, sticky="w", padx=4)
        ttk.Entry(dw, textvariable=self.assigned_date_var, width=16).pack(side="left")
        ttk.Button(dw, text="📅", width=2, command=lambda: self.open_date_picker(self.assigned_date_var)).pack(side="left")
        ttk.Label(fee_frame, text="Notes:").grid(row=4, column=0, sticky="w", padx=4)
        self.assign_notes_var = tk.StringVar()
        ttk.Entry(fee_frame, textvariable=self.assign_notes_var, width=34).grid(row=4, column=1, sticky="ew", padx=4)
        ttk.Button(fee_frame, text="Assign Fee", command=self.assign_fee).grid(row=5, column=0, columnspan=2, pady=6)
       
        payment_frame = ttk.LabelFrame(self, text="Record Payment", padding=6)
        payment_frame.pack(fill="x", padx=10, pady=2)
        ttk.Label(payment_frame, text="Fee ID:").grid(row=0, column=0, sticky="w", padx=4)
        self.payment_fee_id_var = tk.StringVar()
        fee_id_frame = ttk.Frame(payment_frame)
        fee_id_frame.grid(row=0, column=1, sticky="w", padx=4)
        ttk.Entry(fee_id_frame, textvariable=self.payment_fee_id_var, width=12).pack(side="left")
        ttk.Button(fee_id_frame, text="📋", width=3, command=self.show_fees_list).pack(side="left", padx=2)
        ttk.Label(payment_frame, text="Payment Amount:").grid(row=1, column=0, sticky="w", padx=4)
        self.payment_amount_var = tk.StringVar()
        ttk.Entry(payment_frame, textvariable=self.payment_amount_var, width=16).grid(row=1, column=1, sticky="w", padx=4)
        ttk.Label(payment_frame, text="Payment Method:").grid(row=2, column=0, sticky="w", padx=4)
        self.payment_method_var = tk.StringVar(value="Cash")
        ttk.Combobox(payment_frame, textvariable=self.payment_method_var, values=["Cash", "Card", "Bank Transfer", "Jazz Cash", "Easy Paisa"], width=16).grid(row=2, column=1, sticky="w", padx=4)
        ttk.Label(payment_frame, text="Payment Date (DD-MM-YYYY):").grid(row=3, column=0, sticky="w", padx=4)
        self.payment_date_var = tk.StringVar()
        pw = ttk.Frame(payment_frame); pw.grid(row=3, column=1, sticky="w", padx=4)
        ttk.Entry(pw, textvariable=self.payment_date_var, width=16).pack(side="left")
        ttk.Button(pw, text="📅", width=2, command=lambda: self.open_date_picker(self.payment_date_var)).pack(side="left")
        ttk.Button(payment_frame, text="Record Payment", command=self.record_payment).grid(row=4, column=0, columnspan=2, pady=6)
       
        self.populate_dropdowns()
   
    def populate_dropdowns(self):
        self.populate_members_dropdown()
        ftypes = self.database.get_fee_types()
        self.fee_type_combo['values'] = [f"{ft['fee_type_id']} - {ft['fee_name']}" for ft in ftypes]

    def populate_members_dropdown(self):
        members = self.database.get_all_members()
        self.member_combo['values'] = [f"{m['member_id']} - {m['name']}" for m in members]
   
    def show_fees_list(self):
        """Show available fees in a popup window"""
        try:
            fees = self.database.get_all_fees_direct()
            if not fees:
                messagebox.showinfo("Info", "No fees found. Please assign fees to members first.")
                return
           
            win = tk.Toplevel(self)
            win.title("Available Fees - Select Fee ID")
            win.geometry("700x400")
           
            ttk.Label(win, text="Double-click a fee to select its Fee ID", font=("Arial", 10, "bold")).pack(pady=5)
           
            cols = ("Fee ID", "Member", "Fee Type", "Total", "Paid", "Pending", "Status")
            tree = ttk.Treeview(win, columns=cols, show="headings", height=15)
            for c in cols:
                tree.heading(c, text=c)
                tree.column(c, width=100)
           
            for f in fees:
                total = f.get('total_amount') or 0.0
                paid = f.get('paid_amount') or 0.0
                pending = total - paid
                tree.insert("", "end", values=(
                    f['fee_id'], f['member_name'], f['fee_name'],
                    f"PKR {total:.2f}", f"PKR {paid:.2f}", f"PKR {pending:.2f}",
                    f.get('payment_status') or 'Pending'
                ))
           
            def on_double_click(event):
                sel = tree.selection()
                if sel:
                    item = tree.item(sel[0])
                    fee_id = item['values'][0]
                    self.payment_fee_id_var.set(str(fee_id))
                    win.destroy()
           
            tree.bind("<Double-1>", on_double_click)
            tree.pack(fill="both", expand=True, padx=10, pady=5)
            scrollbar = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
            scrollbar.pack(side="right", fill="y")
            tree.configure(yscrollcommand=scrollbar.set)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load fees: {str(e)}")
   
    def assign_fee(self):
        if not self.member_var.get() or not self.fee_type_var.get():
            messagebox.showerror("Error", "Please select member and fee type!")
            return
        if not self.amount_var.get().strip():
            messagebox.showerror("Error", "Please enter amount!")
            return
        try:
            amount = float(self.amount_var.get())
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be greater than 0!")
                return
            member_id = int(self.member_var.get().split(" - ")[0])
            fee_type_id = int(self.fee_type_var.get().split(" - ")[0])
            date_iso = self.parse_ddmmyyyy_to_iso(self.assigned_date_var.get().strip())
           
            fee_id = self.database.assign_fee_to_member(member_id, fee_type_id, amount, date_iso, self.assign_notes_var.get().strip())
           
            if fee_id:
                # Clear form
                self.amount_var.set("")
                self.assigned_date_var.set("")
                self.assign_notes_var.set("")
               
                # Force refresh fees list immediately
                if self.fees_frame:
                    try:
                        self.fees_frame.refresh_fees_list()
                    except Exception as e:
                        print(f"Error refreshing fees list: {e}")
               
                # Also refresh dashboard
                if self.dashboard_frame:
                    try:
                        self.dashboard_frame.refresh_stats()
                    except Exception as e:
                        print(f"Error refreshing dashboard: {e}")
               
                messagebox.showinfo("Success", f"Fee assigned successfully!\nFee ID: {fee_id}\nAmount: PKR {amount:.2f}")
            else:
                messagebox.showerror("Error", "Failed to assign fee!")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to assign fee:\n{str(e)}")
            import traceback
            print(traceback.format_exc())
   
    def record_payment(self):
        try:
            # Validate inputs
            fee_id_str = self.payment_fee_id_var.get().strip()
            amount_str = self.payment_amount_var.get().strip()
           
            if not fee_id_str:
                messagebox.showerror("Error", "Please enter Fee ID!")
                return
            if not amount_str:
                messagebox.showerror("Error", "Please enter Payment Amount!")
                return
           
            try:
                fee_id = int(fee_id_str)
            except ValueError:
                messagebox.showerror("Error", f"Invalid Fee ID: '{fee_id_str}'. Please enter a valid number.")
                return
           
            try:
                amount = float(amount_str)
            except ValueError:
                messagebox.showerror("Error", f"Invalid Payment Amount: '{amount_str}'. Please enter a valid number.")
                return
           
            if amount <= 0:
                messagebox.showerror("Error", "Payment amount must be greater than 0!")
                return
           
            date_iso = self.parse_ddmmyyyy_to_iso(self.payment_date_var.get().strip())
            method = self.payment_method_var.get() or "Cash"
           
            # Record payment - this will raise exception if fee_id doesn't exist
            try:
                self.database.add_payment(fee_id, amount, method, "", date_iso)
            except ValueError as ve:
                messagebox.showerror("Error", str(ve))
                return
            except Exception as db_error:
                messagebox.showerror("Database Error", f"Failed to record payment in database:\n{str(db_error)}")
                import traceback
                print(traceback.format_exc())
                return
           
            # Clear form
            self.payment_fee_id_var.set("")
            self.payment_amount_var.set("")
            self.payment_date_var.set("")
           
            # Force refresh all views - ensure they happen
            refresh_errors = []
           
            # Refresh Member Fees list
            if self.fees_frame:
                try:
                    self.fees_frame.refresh_fees_list()
                    print("✓ Member Fees list refreshed")
                except Exception as e:
                    error_msg = f"Failed to refresh fees list: {e}"
                    refresh_errors.append(error_msg)
                    print(f"✗ {error_msg}")
                    import traceback
                    traceback.print_exc()
            else:
                print("⚠ fees_frame not available for refresh")
           
            # Refresh Dashboard
            if self.dashboard_frame:
                try:
                    self.dashboard_frame.refresh_stats()
                    print("✓ Dashboard refreshed")
                except Exception as e:
                    error_msg = f"Failed to refresh dashboard: {e}"
                    refresh_errors.append(error_msg)
                    print(f"✗ {error_msg}")
                    import traceback
                    traceback.print_exc()
            else:
                print("⚠ dashboard_frame not available for refresh")
           
            # Refresh Payment section dropdowns (in case member list changed)
            try:
                self.populate_dropdowns()
                print("✓ Payment dropdowns refreshed")
            except Exception as e:
                print(f"⚠ Failed to refresh dropdowns: {e}")
           
            # Show success message
            success_msg = f"Payment of PKR {amount:.2f} recorded successfully!\nFee ID: {fee_id}"
            if refresh_errors:
                success_msg += f"\n\nNote: Some views may not have refreshed:\n" + "\n".join(refresh_errors)
            messagebox.showinfo("Success", success_msg)
        except Exception as e:
            import traceback
            error_msg = f"Unexpected error:\n{str(e)}\n\n{traceback.format_exc()}"
            messagebox.showerror("Error", error_msg)
            print(error_msg)


class AllPaymentsHistoryFrame(ttk.Frame):
    """Naya page jo Payments aur Search ke darmiyan add kiya gaya hai"""
    def __init__(self, parent, database: GymDatabase):
        super().__init__(parent)
        self.database = database
        self.setup_ui()
        self.refresh_history()


    def setup_ui(self):
        ttk.Label(self, text="All Members Payment History", font=("Arial", 16, "bold")).pack(pady=10)
        list_frame = ttk.Frame(self, padding=10)
        list_frame.pack(fill="both", expand=True)


        cols = ("Member Name", "Member ID", "Fee ID", "Fee Type", "Total", "Paid", "Pending", "Status", "Assign Date", "Paid Date")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=20)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
       
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        ttk.Button(self, text="Refresh History", command=self.refresh_history).pack(pady=5)


    def refresh_history(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        members = self.database.get_all_members()
        for m in members:
            fees = self.database.get_member_fees(m['member_id'])
            for f in fees:
                pending = f['total_amount'] - f['paid_amount']
                self.tree.insert("", "end", values=(
                    m['name'], m['member_id'], f['fee_id'], f['fee_name'],
                    f"PKR {f['total_amount']:.2f}", f"PKR {f['paid_amount']:.2f}", f"PKR {pending:.2f}",
                    f['payment_status'], (f.get('created_date') or '')[:10], (f.get('last_payment_date') or '')[:10]
                ))


class DashboardFrame(ttk.Frame):
    def __init__(self, parent, database: GymDatabase):
        super().__init__(parent)
        self.database = database
        self.setup_ui()
        self.refresh_stats()
        self.after(5000, self._auto_refresh)
   
    def setup_ui(self):
        ttk.Label(self, text="Dashboard", font=("Arial", 16, "bold")).pack(pady=10)
        stats_frame = ttk.Frame(self); stats_frame.pack(fill="x", padx=20, pady=10)
        self.create_stat_box(stats_frame, "Total Members", "0", 0, 0)
        self.create_stat_box(stats_frame, "Pending Payments", "0", 0, 1)
        self.create_stat_box(stats_frame, "Total Fees", "PKR 0.00", 0, 2)
        self.create_stat_box(stats_frame, "Total Paid", "PKR 0.00", 1, 0)
        self.create_stat_box(stats_frame, "Total Pending", "PKR 0.00", 1, 1)
        breakdown_frame = ttk.LabelFrame(self, text="Payment Status Breakdown", padding=10)
        breakdown_frame.pack(fill="x", padx=20, pady=10)
        self.status_tree = ttk.Treeview(breakdown_frame, columns=("Status", "Count"), show="headings", height=5)
        self.status_tree.heading("Status", text="Status"); self.status_tree.heading("Count", text="Count")
        self.status_tree.pack(fill="x")
        ttk.Button(self, text="Export Payment Report to Excel", command=self.export_payments).pack(pady=10)
   
    def create_stat_box(self, parent, title, value, row, col):
        box = ttk.LabelFrame(parent, text=title, padding=10); box.grid(row=row, column=col, padx=10, pady=5, sticky="ew")
        val_label = ttk.Label(box, text=value, font=("Arial", 18, "bold")); val_label.pack()
        setattr(self, f"{title.lower().replace(' ', '_')}_label", val_label)
        parent.columnconfigure(col, weight=1)
   
    def refresh_stats(self):
        stats = self.database.get_dashboard_stats()
        t_fees = stats.get('total_fees') or 0
        t_paid = stats.get('total_paid') or 0
        t_pending = stats.get('total_pending') or 0
        self.total_members_label.config(text=str(stats.get('total_members') or 0))
        self.pending_payments_label.config(text=str(t_pending))
        self.total_fees_label.config(text=f"PKR {t_fees:.2f}")
        self.total_paid_label.config(text=f"PKR {t_paid:.2f}")
        self.total_pending_label.config(text=f"PKR {t_pending:.2f}")
        for item in self.status_tree.get_children(): self.status_tree.delete(item)
        for status, count in (stats.get('status_breakdown') or {}).items():
            self.status_tree.insert("", "end", values=(str(status or ""), str(count or 0)))


    def _auto_refresh(self):
        try: self.refresh_stats()
        finally: self.after(5000, self._auto_refresh)
   
    def export_payments(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if filename: self.database.export_payment_report_to_excel(filename)


class SearchFrame(ttk.Frame):
    def __init__(self, parent, database: GymDatabase):
        super().__init__(parent)
        self.database = database
        self.setup_ui()
   
    def setup_ui(self):
        ttk.Label(self, text="Search & Reports", font=("Arial", 16, "bold")).pack(pady=10)
        sf = ttk.LabelFrame(self, text="Search Members", padding=10); sf.pack(fill="x", padx=10, pady=5)
        self.search_var = tk.StringVar()
        ttk.Entry(sf, textvariable=self.search_var, width=40).pack(side="left", padx=5)
        ttk.Button(sf, text="Search", command=self.search_members).pack(side="left")
        ttk.Button(sf, text="Clear", command=self.clear_search).pack(side="left", padx=5)
       
        self.search_tree = ttk.Treeview(self, columns=("ID", "Name", "Phone", "Payment Status", "Total Fees", "Paid Amount", "Pending Amount"), show="headings", height=8)
        for col in self.search_tree["columns"]: self.search_tree.heading(col, text=col); self.search_tree.column(col, width=100)
        self.search_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.search_tree.bind("<Double-1>", self.on_member_select)


        df = ttk.LabelFrame(self, text="Member Details & History", padding=10); df.pack(fill="x", padx=10, pady=5)
        self.detail_name_var = tk.StringVar(); ttk.Label(df, text="Selected:").pack(side="left")
        ttk.Entry(df, textvariable=self.detail_name_var, state="readonly").pack(side="left", padx=5)
        ttk.Button(df, text="Export Member Report", command=self.export_member_report).pack(side="left")


        self.history_tree = ttk.Treeview(self, columns=("Fee ID", "Type", "Total", "Paid", "Pending", "Status", "Date"), show="headings", height=5)
        for col in self.history_tree["columns"]: self.history_tree.heading(col, text=col); self.history_tree.column(col, width=100)
        self.history_tree.pack(fill="both", expand=True, padx=10, pady=5)


    def search_members(self):
        term = self.search_var.get().strip()
        for i in self.search_tree.get_children():
            self.search_tree.delete(i)
        results = self.database.search_members(term)
        for m in results:
            summary = self.get_member_payment_summary(m['member_id'])
            self.search_tree.insert("", "end", values=(m['member_id'], m['name'], m['phone'], summary['status'], f"PKR {summary['total_fees']:.2f}", f"PKR {summary['paid_amount']:.2f}", f"PKR {summary['pending_amount']:.2f}"))


    def get_member_payment_summary(self, member_id):
        det = self.database.get_member_comprehensive_details(member_id)
        if not det or not det['fees']: return {'status':'No Fees', 'total_fees':0.0, 'paid_amount':0.0, 'pending_amount':0.0}
        tf = sum(f['total_amount'] for f in det['fees']); tp = sum(f['paid_amount'] for f in det['fees'])
        return {'status': 'Paid' if tf-tp<=0 else 'Partial' if tp>0 else 'Pending', 'total_fees':tf, 'paid_amount':tp, 'pending_amount':tf-tp}


    def clear_search(self):
        self.search_var.set("")
        for i in self.search_tree.get_children(): self.search_tree.delete(i)
        for i in self.history_tree.get_children(): self.history_tree.delete(i)
        self.detail_name_var.set("")


    def on_member_select(self, event):
        sel = self.search_tree.selection()
        if not sel: return
        item = self.search_tree.item(sel[0]); mid = item['values'][0]
        self.detail_name_var.set(item['values'][1])
        for i in self.history_tree.get_children(): self.history_tree.delete(i)
        det = self.database.get_member_comprehensive_details(mid)
        for f in det['fees']:
            self.history_tree.insert("", "end", values=(f['fee_id'], f['fee_name'], f['total_amount'], f['paid_amount'], f['total_amount']-f['paid_amount'], f['payment_status'], (f.get('created_date') or '')[:10]))


    def export_member_report(self):
        sel = self.search_tree.selection()
        if sel:
            mid = self.search_tree.item(sel[0])['values'][0]
            fn = filedialog.asksaveasfilename(defaultextension=".xlsx")
            if fn: self.database.export_member_details_to_excel(mid, fn)


class MemberFeesFrame(ttk.Frame):
    def __init__(self, parent, database: GymDatabase):
        super().__init__(parent)
        self.database = database
        self.setup_ui()
        self.refresh_fees_list()
   
    def setup_ui(self):
        ttk.Label(self, text="Member Fees Management", font=("Arial", 16, "bold")).pack(pady=10)
        lf = ttk.LabelFrame(self, text="All Member Fees", padding=10); lf.pack(fill="both", expand=True, padx=10, pady=5)
        cols = ("Fee ID", "Member", "Fee Type", "Total", "Paid", "Pending", "Status", "Payment Method", "Assign Date", "Paid Date", "Notes")
        self.fees_tree = ttk.Treeview(lf, columns=cols, show="headings", height=20)
        for c in cols: self.fees_tree.heading(c, text=c); self.fees_tree.column(c, width=100)
        sb = ttk.Scrollbar(lf, orient="vertical", command=self.fees_tree.yview)
        self.fees_tree.configure(yscrollcommand=sb.set); self.fees_tree.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
        af = ttk.Frame(self); af.pack(fill="x", padx=10, pady=5)
        ttk.Button(af, text="Export to Excel", command=self.export_fees).pack(side="left", padx=5)
   
    def refresh_fees_list(self):
        try:
            # Clear existing items
            for i in self.fees_tree.get_children():
                self.fees_tree.delete(i)
           
            # Use direct query to get all fees at once (more reliable)
            try:
                all_fees = self.database.get_all_fees_direct()
                if all_fees:
                    for f in all_fees:
                        total = f.get('total_amount') if f.get('total_amount') is not None else 0.0
                        paid = f.get('paid_amount') if f.get('paid_amount') is not None else 0.0
                        pending = total - paid
                        fee_name = f.get('fee_name', 'Unknown')
                        member_name = f.get('member_name', 'Unknown')
                        payment_status = f.get('payment_status') or 'Pending'
                        payment_method = f.get('last_payment_method') or 'N/A'
                        created_date = (f.get('created_date') or '')[:10] if f.get('created_date') else ''
                        last_payment_date = (f.get('last_payment_date') or '')[:10] if f.get('last_payment_date') else ''
                        notes = f.get('notes', '')
                       
                        self.fees_tree.insert("", "end", values=(
                            f.get('fee_id', ''),
                            member_name,
                            fee_name,
                            f"PKR {total:.2f}",
                            f"PKR {paid:.2f}",
                            f"PKR {pending:.2f}",
                            payment_status,
                            payment_method,
                            created_date,
                            last_payment_date,
                            notes
                        ))
                else:
                    # Fallback: try member-by-member approach
                    members = self.database.get_all_members()
                    if members:
                        for m in members:
                            try:
                                fees = self.database.get_member_fees(m['member_id'])
                                if fees:
                                    for f in fees:
                                        total = f.get('total_amount') if f.get('total_amount') is not None else 0.0
                                        paid = f.get('paid_amount') if f.get('paid_amount') is not None else 0.0
                                        pending = total - paid
                                        fee_name = f.get('fee_name', 'Unknown')
                                        payment_status = f.get('payment_status') or 'Pending'
                                        payment_method = f.get('last_payment_method') or 'N/A'
                                        created_date = (f.get('created_date') or '')[:10] if f.get('created_date') else ''
                                        last_payment_date = (f.get('last_payment_date') or '')[:10] if f.get('last_payment_date') else ''
                                        notes = f.get('notes', '')
                                       
                                        self.fees_tree.insert("", "end", values=(
                                            f.get('fee_id', ''),
                                            m.get('name', 'Unknown'),
                                            fee_name,
                                            f"PKR {total:.2f}",
                                            f"PKR {paid:.2f}",
                                            f"PKR {pending:.2f}",
                                            payment_status,
                                            payment_method,
                                            created_date,
                                            last_payment_date,
                                            notes
                                        ))
                            except Exception as e:
                                print(f"Error loading fees for member {m.get('member_id')}: {e}")
                                continue
            except Exception as e:
                print(f"Error in get_all_fees_direct: {e}")
                import traceback
                traceback.print_exc()
        except Exception as e:
            print(f"Error in refresh_fees_list: {e}")
            import traceback
            traceback.print_exc()


    def export_fees(self):
        fn = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if fn: self.database.export_payment_report_to_excel(fn)
