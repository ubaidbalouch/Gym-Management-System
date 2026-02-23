import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os


# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from database import GymDatabase
from ui_components import (
    MemberManagementFrame,
    PaymentManagementFrame,
    DashboardFrame,
    MemberFeesFrame,
)


class GymManagementApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Gym Management Software")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
       
        # Initialize database
        self.database = GymDatabase()
       
        # Setup UI
        self.setup_ui()
       
        # Center window on screen
        self.center_window()
   
    def setup_ui(self):
        """Setup the main application UI"""
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
       
        # Main title
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill="x", padx=20, pady=10)
       
        title_label = ttk.Label(
            title_frame,
            text="🏋️ GYM MANAGEMENT SOFTWARE",
            font=("Arial", 20, "bold"),
            foreground="#2E86AB"
        )
        title_label.pack()
       
        subtitle_label = ttk.Label(
            title_frame,
            text="Complete Member & Payment Management System (PKR Currency)",
            font=("Arial", 12),
            foreground="#666666"
        )
        subtitle_label.pack(pady=5)
       
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
       
        # Create tabs
        self.create_tabs()
       
        # Status bar
        self.create_status_bar()
       
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
   
    def create_tabs(self):
        """Create all application tabs"""
        # Dashboard Tab
        self.dashboard_frame = DashboardFrame(self.notebook, self.database)
        self.notebook.add(self.dashboard_frame, text="📊 Dashboard")
       
        # Member Management Tab
        self.member_frame = MemberManagementFrame(self.notebook, self.database)
        self.notebook.add(self.member_frame, text="👥 Members")
       
        # Member Fees Tab (all fees list - refreshes when payment is recorded)
        self.fees_frame = MemberFeesFrame(self.notebook, self.database)
        self.notebook.add(self.fees_frame, text="📋 Member Fees")
       
        # Payment Management Tab (pass fees_frame & dashboard so lists refresh after payment)
        self.payment_frame = PaymentManagementFrame(
            self.notebook, self.database,
            fees_frame=self.fees_frame,
            dashboard_frame=self.dashboard_frame,
        )
        self.notebook.add(self.payment_frame, text="💰 Payments (PKR)")
       
        # Help Tab
        self.help_frame = self.create_help_tab()
        self.notebook.add(self.help_frame, text="❓ Help")
   
    def _on_tab_changed(self, event):
        """Auto-refresh Member Fees list when user switches to that tab."""
        try:
            current = self.notebook.index(self.notebook.select())
            if current == 2:  # Member Fees tab index
                self.fees_frame.refresh_fees_list()
        except Exception:
            pass
   
    def create_help_tab(self):
        """Create help tab with usage instructions"""
        help_frame = ttk.Frame(self.notebook)
       
        # Help content
        help_text = """
🏋️ GYM MANAGEMENT SOFTWARE - USER GUIDE


📊 DASHBOARD:
• View total members, pending payments, and financial summaries
• Export member lists and payment reports to CSV
• Monitor payment status breakdown (PKR only)


👥 MEMBER MANAGEMENT:
• Add new members with details (Name, Phone only)
• Each member gets a unique Member ID automatically
• Edit or delete members easily
• View all members in an organized table


💰 PAYMENT MANAGEMENT:
• Assign fees to members (Membership, Personal Training, Supplement fees)
• Record payments with multiple payment methods
• Track payment status (Pending, Partial Paid, Paid)
• View all member fees and payment history
• Automatic calculation of pending amounts in PKR


💡 TIPS:
• Double-click on members in lists to edit them
• Use the search function to quickly find specific members
• Export reports regularly for backup and analysis
• All data is automatically saved to the local SQLite database


📁 EXPORTING:
• CSV exports include all relevant data
• Choose save location when exporting
• Reports can be opened in Excel or other spreadsheet applications
        """
       
        # Create text widget with scrollbar
        text_frame = ttk.Frame(help_frame)
        text_frame.pack(fill="both", expand=True, padx=20, pady=20)
       
        help_text_widget = tk.Text(
            text_frame,
            wrap="word",
            font=("Consolas", 10),
            bg="#f8f9fa",
            relief="flat",
            padx=15,
            pady=15
        )
       
        help_text_widget.insert("1.0", help_text)
        help_text_widget.config(state="disabled")  # Make read-only
       
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=help_text_widget.yview)
        help_text_widget.configure(yscrollcommand=scrollbar.set)
       
        help_text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
       
        return help_frame
   
    def create_status_bar(self):
        """Create status bar at bottom of application"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", side="bottom")
       
        # Separator
        separator = ttk.Separator(status_frame, orient="horizontal")
        separator.pack(fill="x")
       
        # Status content
        status_content = ttk.Frame(status_frame)
        status_content.pack(fill="x", padx=10, pady=5)
       
        # Database status
        db_status = ttk.Label(
            status_content,
            text="✅ Database: Connected",
            font=("Arial", 9),
            foreground="green"
        )
        db_status.pack(side="left")
       
        # Version info
        version_label = ttk.Label(
            status_content,
            text="v1.0.1 | Built with Python & Tkinter | Currency: PKR",
            font=("Arial", 9),
            foreground="#666666"
        )
        version_label.pack(side="right")
   
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
   
    def on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Are you sure you want to quit the application?"):
            self.root.destroy()
   
    def run(self):
        """Start the application"""
        try:
            self.root.mainloop()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            print(f"Error: {e}")


def main():
    """Main entry point"""
    try:
        app = GymManagementApp()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        messagebox.showerror("Startup Error", f"Failed to start application:\n{str(e)}")


if __name__ == "__main__":
    main()





