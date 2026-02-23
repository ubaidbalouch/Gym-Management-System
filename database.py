import sqlite3
from datetime import date
import sys
import os


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller EXE"""
    try:
        # PyInstaller temporary folder
        base_path = sys._MEIPASS
    except AttributeError:
        # Development environment
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)




class GymDatabase:
    def __init__(self, db_path=None):
        # Use production-safe path
        self.db_path = resource_path(db_path or "gym.db")
        self.create_tables()


    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn


    def create_tables(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS members
                         (member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                          name TEXT, phone TEXT, registration_date TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS fee_types
                          (fee_type_id INTEGER PRIMARY KEY AUTOINCREMENT, fee_name TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS member_fees
                         (fee_id INTEGER PRIMARY KEY AUTOINCREMENT, member_id INTEGER,
                          fee_type_id INTEGER, total_amount REAL, paid_amount REAL DEFAULT 0,
                          payment_status TEXT, created_date TEXT, notes TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS payments
                         (payment_id INTEGER PRIMARY KEY AUTOINCREMENT, fee_id INTEGER,
                          amount REAL, payment_method TEXT, notes TEXT, payment_date TEXT)''')
       
        try:
            cursor.execute("ALTER TABLE member_fees ADD COLUMN last_payment_date TEXT")
        except sqlite3.OperationalError:
            pass  # column already exists
       
        # Initialize default fee types
        cursor.execute("SELECT COUNT(*) FROM fee_types")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("INSERT INTO fee_types (fee_name) VALUES (?)",
                               [('Monthly Fee',), ('Admission Fee',), ('Personal Training',), ('Supplement Fee',)])
        else:
            cursor.execute("SELECT fee_type_id FROM fee_types WHERE fee_name = ?", ('Supplement Fee',))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO fee_types (fee_name) VALUES (?)", ('Supplement Fee',))
       
        conn.commit()
        conn.close()


    # ---------------- Member Methods ----------------
    def get_all_members(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows


    def get_member_by_id(self, member_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE member_id = ?", (member_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None


    def search_members(self, term):
        conn = self.connect()
        cursor = conn.cursor()
        q = f"%{term}%"
        cursor.execute("SELECT * FROM members WHERE name LIKE ? OR phone LIKE ? OR member_id LIKE ?", (q, q, q))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows


    def add_member(self, name, phone):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO members (name, phone, registration_date) VALUES (?, ?, ?)",
                       (name, phone, date.today().isoformat()))
        mid = cursor.lastrowid
        conn.commit()
        conn.close()
        return mid


    def update_member(self, mid, name, phone):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("UPDATE members SET name=?, phone=? WHERE member_id=?", (name, phone, mid))
        conn.commit()
        conn.close()
        return True


    def delete_member(self, mid):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM members WHERE member_id=?", (mid,))
        cursor.execute("DELETE FROM member_fees WHERE member_id=?", (mid,))
        conn.commit()
        conn.close()
        return True
   
    def delete_all_members(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM payments")
        cursor.execute("DELETE FROM member_fees")
        cursor.execute("DELETE FROM members")
        conn.commit()
        conn.close()
        return True


    # ---------------- Fee Methods ----------------
    def get_fee_types(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM fee_types")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows


    def assign_fee_to_member(self, mid, fid, amt, cdate, notes):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            member_id = int(mid)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid member ID: {mid}")
       
        cursor.execute("SELECT member_id FROM members WHERE member_id = ?", (member_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Member ID {member_id} does not exist!")
       
        cursor.execute("INSERT INTO member_fees (member_id, fee_type_id, total_amount, payment_status, created_date, notes) VALUES (?,?,?,?,?,?)",
                       (member_id, fid, amt, 'Pending', cdate or date.today().isoformat(), notes))
        last_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return last_id


    def add_payment(self, fee_id, amt, method, notes, pdate):
        pdate_iso = pdate or date.today().isoformat()
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT fee_id, total_amount, paid_amount FROM member_fees WHERE fee_id = ?", (fee_id,))
        fee_row = cursor.fetchone()
        if not fee_row:
            conn.close()
            raise ValueError(f"Fee ID {fee_id} does not exist!")
       
        current_paid = fee_row['paid_amount'] or 0.0
        total_amount = fee_row['total_amount'] or 0.0
        new_paid = current_paid + amt
        new_status = 'Paid' if new_paid >= total_amount else ('Partial' if new_paid > 0 else 'Pending')
       
        cursor.execute("INSERT INTO payments (fee_id, amount, payment_method, notes, payment_date) VALUES (?,?,?,?,?)",
                       (fee_id, amt, method, notes, pdate_iso))
       
        cursor.execute("""UPDATE member_fees SET paid_amount = ?, payment_status = ?, last_payment_date = ? WHERE fee_id = ?""",
                       (new_paid, new_status, pdate_iso, fee_id))
        conn.commit()
        conn.close()
        return True


    def get_member_fees(self, mid):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""SELECT mf.*, ft.fee_name,
                         (SELECT payment_method FROM payments WHERE fee_id = mf.fee_id ORDER BY payment_id DESC LIMIT 1) as last_payment_method
                         FROM member_fees mf
                         LEFT JOIN fee_types ft ON mf.fee_type_id = ft.fee_type_id
                         WHERE mf.member_id = ? ORDER BY mf.fee_id DESC""", (mid,))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows


    def get_all_fees_direct(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""SELECT mf.*, ft.fee_name, m.name as member_name,
                         (SELECT payment_method FROM payments WHERE fee_id = mf.fee_id ORDER BY payment_id DESC LIMIT 1) as last_payment_method
                         FROM member_fees mf
                         LEFT JOIN fee_types ft ON mf.fee_type_id = ft.fee_type_id
                         LEFT JOIN members m ON mf.member_id = m.member_id
                         ORDER BY mf.fee_id DESC""")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows


    # ---------------- Dashboard & Export ----------------
    def get_dashboard_stats(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM members")
        total_m = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(total_amount), SUM(paid_amount) FROM member_fees")
        res = cursor.fetchone()
        t_fees, t_paid = (res[0] or 0, res[1] or 0)
        cursor.execute("SELECT payment_status, COUNT(*) FROM member_fees GROUP BY payment_status")
        breakdown = {r[0]: r[1] for r in cursor.fetchall() if r[0]}
        conn.close()
        return {'total_members': total_m, 'total_fees': t_fees, 'total_paid': t_paid,
                'total_pending': t_fees - t_paid, 'status_breakdown': breakdown}


    def export_member_details_to_excel(self, member_id, filename):
        try:
            import pandas as pd
        except ImportError:
            return False
        conn = self.connect()
        query = """SELECT m.name as 'Member Name', mf.fee_id as 'Fee ID', ft.fee_name as 'Type',
                   mf.total_amount as 'Total', mf.paid_amount as 'Paid', (mf.total_amount - mf.paid_amount) as 'Pending',
                   mf.payment_status as 'Status',
                   (SELECT payment_method FROM payments WHERE fee_id = mf.fee_id ORDER BY payment_id DESC LIMIT 1) as 'Method'
                   FROM member_fees mf
                   LEFT JOIN fee_types ft ON mf.fee_type_id = ft.fee_type_id
                   LEFT JOIN members m ON mf.member_id = m.member_id
                   WHERE mf.member_id = ? ORDER BY mf.fee_id DESC"""
        df = pd.read_sql_query(query, conn, params=(member_id,))
        if not df.empty:
            df['Method'] = df['Method'].fillna('N/A')
            df.to_excel(filename, index=False)
        conn.close()
        return True


    def export_payment_report_to_excel(self, filename):
        try:
            import pandas as pd
        except ImportError:
            return False
        conn = self.connect()
        query = """SELECT m.name as 'Member Name', ft.fee_name as 'Fee Type',
                  (SELECT payment_method FROM payments WHERE fee_id = mf.fee_id ORDER BY payment_id DESC LIMIT 1) as 'Payment Method',
                  mf.payment_status as 'Status', mf.created_date as 'Fee Date', mf.total_amount as 'Total Amount',
                  mf.paid_amount as 'Paid Amount', (mf.total_amount - mf.paid_amount) as 'Pending'
                  FROM member_fees mf
                  LEFT JOIN fee_types ft ON mf.fee_type_id = ft.fee_type_id
                  LEFT JOIN members m ON mf.member_id = m.member_id
                  ORDER BY mf.fee_id DESC"""
        df = pd.read_sql_query(query, conn)
        df['Payment Method'] = df['Payment Method'].fillna('N/A')
        df.to_excel(filename, index=False)
        conn.close()
        return True



