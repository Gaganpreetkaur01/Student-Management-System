import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
from datetime import datetime

DB_NAME = 'student_management_advanced.db'


class DatabaseManager:
    def __init__(self, db_name=DB_NAME):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        cur = self.conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                gender TEXT,
                dob TEXT,
                phone TEXT,
                email TEXT,
                course TEXT,
                department TEXT,
                semester TEXT,
                address TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                status TEXT NOT NULL,
                UNIQUE(student_id, date),
                FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS marks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                max_marks INTEGER NOT NULL,
                obtained_marks INTEGER NOT NULL,
                UNIQUE(student_id, subject),
                FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS fees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                total_fee REAL NOT NULL,
                paid_fee REAL NOT NULL,
                due_fee REAL NOT NULL,
                last_payment_date TEXT,
                UNIQUE(student_id),
                FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
            )
        ''')
        cur.execute('SELECT * FROM users WHERE username=?', ('admin',))
        if not cur.fetchone():
            cur.execute(
                'INSERT INTO users(username, password, role) VALUES (?, ?, ?)',
                ('admin', 'admin123', 'admin')
            )
        self.conn.commit()

    def execute(self, query, params=(), fetch=False, many=False):
        cur = self.conn.cursor()
        if many:
            cur.executemany(query, params)
        else:
            cur.execute(query, params)
        self.conn.commit()
        return cur.fetchall() if fetch else cur.lastrowid


class LoginWindow:
    def __init__(self, root, db):
        self.root = root
        self.db = db
        self.root.title('Student Management System - Login')
        self.root.geometry('420x280')
        self.root.configure(bg='#e7f0ff')
        self.build_ui()

    def build_ui(self):
        title = tk.Label(
            self.root,
            text='Student Management',
            font=('Segoe UI', 16, 'bold'),
            bg='#e7f0ff',
            fg='#0b3d91'
        )
        title.pack(pady=10)

        frame = tk.Frame(self.root, bg='white', bd=0, highlightthickness=1,
                         highlightbackground='#c3d4ff')
        frame.pack(pady=5, padx=25, fill='both', expand=True)

        tk.Label(frame, text='Admin Login', font=('Segoe UI', 15, 'bold'),
                 bg='white', fg='#143d73').pack(pady=(15, 5))

        tk.Label(frame, text='Username', bg='white',
                 font=('Segoe UI', 10)).pack(anchor='w', padx=25)
        self.username = tk.Entry(frame, font=('Segoe UI', 10))
        self.username.pack(padx=25, fill='x', pady=3)

        tk.Label(frame, text='Password', bg='white',
                 font=('Segoe UI', 10)).pack(anchor='w', padx=25, pady=(5, 0))
        self.password = tk.Entry(frame, show='*', font=('Segoe UI', 10))
        self.password.pack(padx=25, fill='x', pady=3)

        login_btn = tk.Button(
            frame,
            text='Login',
            command=self.login,
            bg='#1f6feb',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            activebackground='#1558c0',
            relief=tk.FLAT,
            cursor='hand2'
        )
        login_btn.pack(pady=12, ipadx=10, ipady=3)

        tk.Label(
            frame,
            text='Glad to have you here , lets get things done ',
            bg='white',
            fg='gray',
            font=('Segoe UI', 8)
        ).pack(pady=(0, 10))

        def on_enter(e):
            login_btn['bg'] = '#1558c0'

        def on_leave(e):
            login_btn['bg'] = '#1f6feb'

        login_btn.bind('<Enter>', on_enter)
        login_btn.bind('<Leave>', on_leave)

    def login(self):
        user = self.username.get().strip()
        pwd = self.password.get().strip()
        rows = self.db.execute(
            'SELECT * FROM users WHERE username=? AND password=?',
            (user, pwd),
            fetch=True
        )
        if rows:
            self.root.destroy()
            main_root = tk.Tk()
            StudentManagementApp(main_root, self.db, user)
            main_root.mainloop()
        else:
            messagebox.showerror('Login Failed', 'Invalid username or password')


class StudentManagementApp:
    def __init__(self, root, db, current_user):
        self.root = root
        self.db = db
        self.current_user = current_user
        self.root.title('Advanced Student Management System')
        self.root.geometry('1280x760')
        self.root.configure(bg='#e7f0ff')
        self.selected_student_id = None

        self._configure_style()
        self.build_ui()
        self.load_students()
        self.load_dashboard()

    def _configure_style(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass

        style.configure(
            'TNotebook',
            background='#e7f0ff',
            borderwidth=0
        )
        style.configure(
            'TNotebook.Tab',
            font=('Segoe UI', 10, 'bold'),
            padding=[14, 6],
            background='#d9e4ff',
            foreground='#2d3e50'
        )
        style.map(
            'TNotebook.Tab',
            background=[('selected', '#0b3d91')],
            foreground=[('selected', 'white')]
        )

        style.configure(
            'Treeview',
            background='white',
            foreground='#1f2933',
            rowheight=24,
            fieldbackground='white',
            font=('Segoe UI', 9)
        )
        style.configure(
            'Treeview.Heading',
            background='#0b3d91',
            foreground='white',
            font=('Segoe UI', 9, 'bold')
        )
        style.map(
            'Treeview',
            background=[('selected', '#cfe0ff')],
            foreground=[('selected', '#0b3d91')]
        )

        style.configure('Card.TFrame', background='white', relief='flat')

    def build_ui(self):
        header = tk.Frame(self.root, bg='#0b3d91', height=64)
        header.pack(fill='x')

        tk.Label(
            header,
            text='Advanced Student Management System',
            bg='#0b3d91',
            fg='white',
            font=('Segoe UI Semibold', 18)
        ).pack(side='left', padx=20, pady=10)

        tk.Label(
            header,
            text=f'Logged in as: {self.current_user}',
            bg='#0b3d91',
            fg='#d2e3ff',
            font=('Segoe UI', 10)
        ).pack(side='right', padx=20)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=12, pady=12)

        self.dashboard_tab = tk.Frame(self.notebook, bg='#e7f0ff')
        self.student_tab = tk.Frame(self.notebook, bg='#e7f0ff')
        self.attendance_tab = tk.Frame(self.notebook, bg='#e7f0ff')
        self.marks_tab = tk.Frame(self.notebook, bg='#e7f0ff')
        self.fees_tab = tk.Frame(self.notebook, bg='#e7f0ff')
        self.report_tab = tk.Frame(self.notebook, bg='#e7f0ff')

        self.notebook.add(self.dashboard_tab, text='Dashboard')
        self.notebook.add(self.student_tab, text='Students')
        self.notebook.add(self.attendance_tab, text='Attendance')
        self.notebook.add(self.marks_tab, text='Marks')
        self.notebook.add(self.fees_tab, text='Fees')
        self.notebook.add(self.report_tab, text='Reports')

        self.build_dashboard_tab()
        self.build_student_tab()
        self.build_attendance_tab()
        self.build_marks_tab()
        self.build_fees_tab()
        self.build_report_tab()

    def build_dashboard_tab(self):
        container = tk.Frame(self.dashboard_tab, bg='#e7f0ff')
        container.pack(fill='both', expand=True, padx=8, pady=8)

        self.stats_frame = tk.Frame(container, bg='#e7f0ff')
        self.stats_frame.pack(fill='x', padx=4, pady=4)

        text_frame = tk.Frame(container, bg='#e7f0ff')
        text_frame.pack(fill='both', expand=True, padx=4, pady=(4, 0))

        self.dashboard_text = tk.Text(
            text_frame,
            height=20,
            font=('Consolas', 10),
            bg='#fafdff',
            bd=0,
            highlightthickness=1,
            highlightbackground='#c3d4ff'
        )
        self.dashboard_text.pack(fill='both', expand=True)

    def _make_primary_button(self, parent, text, command, color='#0d6efd'):
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            activebackground='#0b5ed7',
            activeforeground='white',
            relief=tk.FLAT,
            padx=10,
            pady=4,
            cursor='hand2'
        )

        def on_enter(e):
            btn['bg'] = '#0b5ed7'

        def on_leave(e):
            btn['bg'] = color

        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        return btn

    def build_student_tab(self):
        container = tk.Frame(self.student_tab, bg='#e7f0ff')
        container.pack(fill='both', expand=True, padx=8, pady=8)

        left = tk.LabelFrame(
            container,
            text='Student Form',
            bg='#fafdff',
            font=('Segoe UI', 11, 'bold'),
            fg='#12355b',
            bd=0,
            highlightthickness=1,
            highlightbackground='#c3d4ff'
        )
        left.pack(side='left', fill='y', padx=(0, 6), pady=4)

        right = tk.LabelFrame(
            container,
            text='Student Records',
            bg='#fafdff',
            font=('Segoe UI', 11, 'bold'),
            fg='#12355b',
            bd=0,
            highlightthickness=1,
            highlightbackground='#c3d4ff'
        )
        right.pack(side='right', fill='both', expand=True, padx=(6, 0), pady=4)

        fields = [
            ('Roll No', 'roll_no'), ('Name', 'name'), ('Gender', 'gender'),
            ('DOB (YYYY-MM-DD)', 'dob'), ('Phone', 'phone'), ('Email', 'email'),
            ('Course', 'course'), ('Department', 'department'),
            ('Semester', 'semester'), ('Address', 'address')
        ]
        self.student_entries = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(
                left,
                text=label,
                bg='#fafdff',
                font=('Segoe UI', 9)
            ).grid(row=i, column=0, padx=10, pady=4, sticky='w')
            if key == 'gender':
                cb = ttk.Combobox(left, values=['Male', 'Female', 'Other'],
                                  state='readonly', width=23)
                cb.grid(row=i, column=1, padx=10, pady=4, sticky='w')
                self.student_entries[key] = cb
            elif key == 'address':
                txt = tk.Text(left, width=25, height=3, font=('Segoe UI', 9))
                txt.grid(row=i, column=1, padx=10, pady=4, sticky='w')
                self.student_entries[key] = txt
            else:
                ent = tk.Entry(left, width=25, font=('Segoe UI', 9))
                ent.grid(row=i, column=1, padx=10, pady=4, sticky='w')
                self.student_entries[key] = ent

        btn_frame = tk.Frame(left, bg='#fafdff')
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=10)

        self._make_primary_button(btn_frame, 'Add', self.add_student, '#198754').pack(side='left', padx=4)
        self._make_primary_button(btn_frame, 'Update', self.update_student, '#0d6efd').pack(side='left', padx=4)
        self._make_primary_button(btn_frame, 'Delete', self.delete_student, '#dc3545').pack(side='left', padx=4)
        self._make_primary_button(btn_frame, 'Clear', self.clear_student_form, '#6c757d').pack(side='left', padx=4)

        search_frame = tk.Frame(right, bg='#fafdff')
        search_frame.pack(fill='x', padx=6, pady=4)
        tk.Label(
            search_frame,
            text='Search',
            bg='#fafdff',
            font=('Segoe UI', 9)
        ).pack(side='left')
        self.search_entry = tk.Entry(search_frame, width=35, font=('Segoe UI', 9))
        self.search_entry.pack(side='left', padx=6)
        self._make_primary_button(search_frame, 'Go', self.search_students, '#0b7285').pack(side='left', padx=2)
        self._make_primary_button(search_frame, 'Show All', self.load_students, '#495057').pack(side='left', padx=2)

        cols = ('ID', 'Roll No', 'Name', 'Gender', 'Phone', 'Email', 'Course', 'Department', 'Semester')
        self.student_tree = ttk.Treeview(right, columns=cols, show='headings', height=18)
        for c in cols:
            self.student_tree.heading(c, text=c)
            width = 80 if c == 'ID' else 120
            self.student_tree.column(c, width=width, anchor='center')

        vsb = ttk.Scrollbar(right, orient='vertical', command=self.student_tree.yview)
        self.student_tree.configure(yscroll=vsb.set)
        self.student_tree.pack(side='left', fill='both', expand=True, padx=(6, 0), pady=(0, 6))
        vsb.pack(side='right', fill='y', padx=(0, 6), pady=(0, 6))

        self.student_tree.tag_configure('oddrow', background='#f4f7ff')
        self.student_tree.tag_configure('evenrow', background='white')
        self.student_tree.bind('<<TreeviewSelect>>', self.on_student_select)

    def build_attendance_tab(self):
        container = tk.Frame(self.attendance_tab, bg='#e7f0ff')
        container.pack(fill='both', expand=True, padx=8, pady=8)

        top = tk.LabelFrame(
            container,
            text='Mark Attendance',
            bg='#fafdff',
            font=('Segoe UI', 11, 'bold'),
            fg='#12355b',
            bd=0,
            highlightthickness=1,
            highlightbackground='#c3d4ff'
        )
        top.pack(fill='x', padx=4, pady=(0, 6))

        tk.Label(top, text='Student Roll No', bg='#fafdff', font=('Segoe UI', 9)).grid(row=0, column=0, padx=6, pady=6)
        self.att_roll = tk.Entry(top, width=18, font=('Segoe UI', 9))
        self.att_roll.grid(row=0, column=1, padx=6, pady=6)

        tk.Label(top, text='Date', bg='#fafdff', font=('Segoe UI', 9)).grid(row=0, column=2, padx=6, pady=6)
        self.att_date = tk.Entry(top, width=18, font=('Segoe UI', 9))
        self.att_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.att_date.grid(row=0, column=3, padx=6, pady=6)

        tk.Label(top, text='Status', bg='#fafdff', font=('Segoe UI', 9)).grid(row=0, column=4, padx=6, pady=6)
        self.att_status = ttk.Combobox(top, values=['Present', 'Absent', 'Leave'], state='readonly', width=15)
        self.att_status.grid(row=0, column=5, padx=6, pady=6)

        self._make_primary_button(top, 'Mark Attendance', self.mark_attendance, '#198754').grid(row=0, column=6, padx=6, pady=6)

        table_frame = tk.Frame(container, bg='#e7f0ff')
        table_frame.pack(fill='both', expand=True, padx=4, pady=(2, 0))

        self.att_tree = ttk.Treeview(table_frame, columns=('Roll No', 'Name', 'Date', 'Status'), show='headings', height=18)
        for c in ('Roll No', 'Name', 'Date', 'Status'):
            self.att_tree.heading(c, text=c)
            self.att_tree.column(c, width=170, anchor='center')

        vsb = ttk.Scrollbar(table_frame, orient='vertical', command=self.att_tree.yview)
        self.att_tree.configure(yscroll=vsb.set)
        self.att_tree.pack(side='left', fill='both', expand=True, padx=(0, 4), pady=(0, 4))
        vsb.pack(side='right', fill='y', pady=(0, 4))

        self.att_tree.tag_configure('oddrow', background='#f4f7ff')
        self.att_tree.tag_configure('evenrow', background='white')

        self.load_attendance()

    def build_marks_tab(self):
        container = tk.Frame(self.marks_tab, bg='#e7f0ff')
        container.pack(fill='both', expand=True, padx=8, pady=8)

        top = tk.LabelFrame(
            container,
            text='Manage Marks',
            bg='#fafdff',
            font=('Segoe UI', 11, 'bold'),
            fg='#12355b',
            bd=0,
            highlightthickness=1,
            highlightbackground='#c3d4ff'
        )
        top.pack(fill='x', padx=4, pady=(0, 6))

        labels = ['Student Roll No', 'Subject', 'Max Marks', 'Obtained']
        self.marks_widgets = []
        for i, label in enumerate(labels):
            tk.Label(top, text=label, bg='#fafdff', font=('Segoe UI', 9)).grid(row=0, column=i*2, padx=5, pady=6)
            ent = tk.Entry(top, width=18, font=('Segoe UI', 9))
            ent.grid(row=0, column=i*2+1, padx=5, pady=6)
            self.marks_widgets.append(ent)

        self._make_primary_button(top, 'Save Marks', self.save_marks, '#0d6efd').grid(row=0, column=8, padx=6)

        table_frame = tk.Frame(container, bg='#e7f0ff')
        table_frame.pack(fill='both', expand=True, padx=4, pady=(2, 0))

        self.marks_tree = ttk.Treeview(
            table_frame,
            columns=('Roll No', 'Name', 'Subject', 'Max', 'Obtained', 'Percentage'),
            show='headings',
            height=18
        )
        for c in ('Roll No', 'Name', 'Subject', 'Max', 'Obtained', 'Percentage'):
            self.marks_tree.heading(c, text=c)
            self.marks_tree.column(c, width=140, anchor='center')

        vsb = ttk.Scrollbar(table_frame, orient='vertical', command=self.marks_tree.yview)
        self.marks_tree.configure(yscroll=vsb.set)
        self.marks_tree.pack(side='left', fill='both', expand=True, padx=(0, 4), pady=(0, 4))
        vsb.pack(side='right', fill='y', pady=(0, 4))

        self.marks_tree.tag_configure('oddrow', background='#f4f7ff')
        self.marks_tree.tag_configure('evenrow', background='white')

        self.load_marks()

    def build_fees_tab(self):
        container = tk.Frame(self.fees_tab, bg='#e7f0ff')
        container.pack(fill='both', expand=True, padx=8, pady=8)

        top = tk.LabelFrame(
            container,
            text='Fee Details',
            bg='#fafdff',
            font=('Segoe UI', 11, 'bold'),
            fg='#12355b',
            bd=0,
            highlightthickness=1,
            highlightbackground='#c3d4ff'
        )
        top.pack(fill='x', padx=4, pady=(0, 6))

        labels = ['Student Roll No', 'Total Fee', 'Paid Fee', 'Last Payment Date']
        self.fee_widgets = []
        for i, label in enumerate(labels):
            tk.Label(top, text=label, bg='#fafdff', font=('Segoe UI', 9)).grid(row=0, column=i*2, padx=5, pady=6)
            ent = tk.Entry(top, width=18, font=('Segoe UI', 9))
            if label == 'Last Payment Date':
                ent.insert(0, datetime.now().strftime('%Y-%m-%d'))
            ent.grid(row=0, column=i*2+1, padx=5, pady=6)
            self.fee_widgets.append(ent)

        self._make_primary_button(top, 'Save Fee Record', self.save_fees, '#fd7e14').grid(row=0, column=8, padx=6)

        table_frame = tk.Frame(container, bg='#e7f0ff')
        table_frame.pack(fill='both', expand=True, padx=4, pady=(2, 0))

        self.fee_tree = ttk.Treeview(
            table_frame,
            columns=('Roll No', 'Name', 'Total', 'Paid', 'Due', 'Last Payment'),
            show='headings',
            height=18
        )
        for c in ('Roll No', 'Name', 'Total', 'Paid', 'Due', 'Last Payment'):
            self.fee_tree.heading(c, text=c)
            self.fee_tree.column(c, width=140, anchor='center')

        vsb = ttk.Scrollbar(table_frame, orient='vertical', command=self.fee_tree.yview)
        self.fee_tree.configure(yscroll=vsb.set)
        self.fee_tree.pack(side='left', fill='both', expand=True, padx=(0, 4), pady=(0, 4))
        vsb.pack(side='right', fill='y', pady=(0, 4))

        self.fee_tree.tag_configure('oddrow', background='#f4f7ff')
        self.fee_tree.tag_configure('evenrow', background='white')

        self.load_fees()

    def build_report_tab(self):
        container = tk.Frame(self.report_tab, bg='#e7f0ff')
        container.pack(fill='both', expand=True, padx=8, pady=8)

        top = tk.Frame(container, bg='#e7f0ff')
        top.pack(fill='x', padx=4, pady=(0, 4))

        self._make_primary_button(top, 'Refresh Reports', self.load_reports, '#6f42c1').pack(side='left', padx=4)
        self._make_primary_button(top, 'Export Students CSV', self.export_students_csv, '#198754').pack(side='left', padx=4)

        self.report_text = tk.Text(
            container,
            font=('Consolas', 10),
            bg='#fafdff',
            bd=0,
            highlightthickness=1,
            highlightbackground='#c3d4ff'
        )
        self.report_text.pack(fill='both', expand=True, padx=4, pady=(4, 0))

        self.load_reports()

    def validate_student_form(self):
        data = {}
        for key, widget in self.student_entries.items():
            if isinstance(widget, tk.Text):
                value = widget.get('1.0', 'end').strip()
            else:
                value = widget.get().strip()
            data[key] = value
        if not data['roll_no'] or not data['name']:
            return None, 'Roll No and Name are required.'
        if data['email'] and '@' not in data['email']:
            return None, 'Invalid email format.'
        if data['phone'] and (not data['phone'].isdigit() or len(data['phone']) < 10):
            return None, 'Phone must contain at least 10 digits.'
        return data, None

    def add_student(self):
        data, error = self.validate_student_form()
        if error:
            messagebox.showerror('Validation Error', error)
            return
        try:
            self.db.execute(
                '''
                INSERT INTO students(roll_no, name, gender, dob, phone, email, course, department, semester, address, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    data['roll_no'], data['name'], data['gender'], data['dob'], data['phone'], data['email'],
                    data['course'], data['department'], data['semester'], data['address'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            )
            messagebox.showinfo('Success', 'Student added successfully')
            self.load_students()
            self.load_dashboard()
            self.load_reports()
            self.clear_student_form()
        except sqlite3.IntegrityError:
            messagebox.showerror('Error', 'Roll number already exists')

    def update_student(self):
        if not self.selected_student_id:
            messagebox.showwarning('Warning', 'Select a student to update')
            return
        data, error = self.validate_student_form()
        if error:
            messagebox.showerror('Validation Error', error)
            return
        try:
            self.db.execute(
                '''
                UPDATE students SET roll_no=?, name=?, gender=?, dob=?, phone=?, email=?,
                                    course=?, department=?, semester=?, address=?
                WHERE id=?
                ''',
                (
                    data['roll_no'], data['name'], data['gender'], data['dob'], data['phone'], data['email'],
                    data['course'], data['department'], data['semester'], data['address'], self.selected_student_id
                )
            )
            messagebox.showinfo('Success', 'Student updated successfully')
            self.load_students()
            self.load_dashboard()
            self.load_reports()
        except sqlite3.IntegrityError:
            messagebox.showerror('Error', 'Roll number already exists')

    def delete_student(self):
        if not self.selected_student_id:
            messagebox.showwarning('Warning', 'Select a student to delete')
            return
        if messagebox.askyesno('Confirm', 'Delete selected student and related records?'):
            self.db.execute('DELETE FROM students WHERE id=?', (self.selected_student_id,))
            self.clear_student_form()
            self.load_students()
            self.load_attendance()
            self.load_marks()
            self.load_fees()
            self.load_dashboard()
            self.load_reports()
            messagebox.showinfo('Deleted', 'Student deleted successfully')

    def clear_student_form(self):
        self.selected_student_id = None
        for key, widget in self.student_entries.items():
            if isinstance(widget, tk.Text):
                widget.delete('1.0', 'end')
            else:
                widget.delete(0, 'end')

    def load_students(self):
        for item in self.student_tree.get_children():
            self.student_tree.delete(item)
        rows = self.db.execute(
            'SELECT id, roll_no, name, gender, phone, email, course, department, semester FROM students ORDER BY id DESC',
            fetch=True
        )
        for index, row in enumerate(rows):
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            self.student_tree.insert('', 'end', values=row, tags=(tag,))

    def search_students(self):
        term = self.search_entry.get().strip()
        for item in self.student_tree.get_children():
            self.student_tree.delete(item)
        rows = self.db.execute(
            '''
            SELECT id, roll_no, name, gender, phone, email, course, department, semester
            FROM students
            WHERE roll_no LIKE ? OR name LIKE ? OR department LIKE ? OR course LIKE ?
            ORDER BY id DESC
            ''',
            (f'%{term}%', f'%{term}%', f'%{term}%', f'%{term}%'),
            fetch=True
        )
        for index, row in enumerate(rows):
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            self.student_tree.insert('', 'end', values=row, tags=(tag,))

    def on_student_select(self, event=None):
        selected = self.student_tree.focus()
        if not selected:
            return
        values = self.student_tree.item(selected, 'values')
        self.selected_student_id = values[0]
        full = self.db.execute(
            '''
            SELECT roll_no, name, gender, dob, phone, email, course, department, semester, address
            FROM students WHERE id=?
            ''',
            (self.selected_student_id,),
            fetch=True
        )
        if full:
            data = full[0]
            keys = ['roll_no', 'name', 'gender', 'dob', 'phone', 'email', 'course', 'department', 'semester', 'address']
            for key, value in zip(keys, data):
                widget = self.student_entries[key]
                if isinstance(widget, tk.Text):
                    widget.delete('1.0', 'end')
                    widget.insert('1.0', value or '')
                else:
                    widget.delete(0, 'end')
                    widget.insert(0, value or '')

    def get_student_by_roll(self, roll_no):
        rows = self.db.execute(
            'SELECT id, name FROM students WHERE roll_no=?',
            (roll_no,),
            fetch=True
        )
        return rows[0] if rows else None

    def mark_attendance(self):
        roll = self.att_roll.get().strip()
        date = self.att_date.get().strip()
        status = self.att_status.get().strip()
        student = self.get_student_by_roll(roll)
        if not student:
            messagebox.showerror('Error', 'Student roll number not found')
            return
        if not date or not status:
            messagebox.showerror('Error', 'Date and status are required')
            return
        try:
            self.db.execute(
                'INSERT OR REPLACE INTO attendance(student_id, date, status) VALUES (?, ?, ?)',
                (student[0], date, status)
            )
            messagebox.showinfo('Success', 'Attendance saved successfully')
            self.load_attendance()
            self.load_dashboard()
            self.load_reports()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def load_attendance(self):
        for item in self.att_tree.get_children():
            self.att_tree.delete(item)
        rows = self.db.execute(
            '''
            SELECT s.roll_no, s.name, a.date, a.status
            FROM attendance a JOIN students s ON a.student_id = s.id
            ORDER BY a.date DESC
            ''',
            fetch=True
        )
        for index, row in enumerate(rows):
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            self.att_tree.insert('', 'end', values=row, tags=(tag,))

    def save_marks(self):
        roll, subject, max_m, obt = [w.get().strip() for w in self.marks_widgets]
        student = self.get_student_by_roll(roll)
        if not student:
            messagebox.showerror('Error', 'Student roll number not found')
            return
        try:
            max_m = int(max_m)
            obt = int(obt)
            if obt > max_m or obt < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror('Error', 'Enter valid marks')
            return
        self.db.execute(
            '''
            INSERT OR REPLACE INTO marks(student_id, subject, max_marks, obtained_marks)
            VALUES (?, ?, ?, ?)
            ''',
            (student[0], subject, max_m, obt)
        )
        messagebox.showinfo('Success', 'Marks saved successfully')
        self.load_marks()
        self.load_dashboard()
        self.load_reports()

    def load_marks(self):
        for item in self.marks_tree.get_children():
            self.marks_tree.delete(item)
        rows = self.db.execute(
            '''
            SELECT s.roll_no, s.name, m.subject, m.max_marks, m.obtained_marks,
                   ROUND((m.obtained_marks * 100.0 / m.max_marks), 2)
            FROM marks m JOIN students s ON m.student_id = s.id
            ORDER BY s.roll_no
            ''',
            fetch=True
        )
        for index, row in enumerate(rows):
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            self.marks_tree.insert('', 'end', values=row, tags=(tag,))

    def save_fees(self):
        roll, total, paid, payment_date = [w.get().strip() for w in self.fee_widgets]
        student = self.get_student_by_roll(roll)
        if not student:
            messagebox.showerror('Error', 'Student roll number not found')
            return
        try:
            total = float(total)
            paid = float(paid)
            if paid > total or total < 0 or paid < 0:
                raise ValueError
            due = total - paid
        except ValueError:
            messagebox.showerror('Error', 'Enter valid fee values')
            return
        self.db.execute(
            '''
            INSERT OR REPLACE INTO fees(student_id, total_fee, paid_fee, due_fee, last_payment_date)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (student[0], total, paid, due, payment_date)
        )
        messagebox.showinfo('Success', 'Fee record saved successfully')
        self.load_fees()
        self.load_dashboard()
        self.load_reports()

    def load_fees(self):
        for item in self.fee_tree.get_children():
            self.fee_tree.delete(item)
        rows = self.db.execute(
            '''
            SELECT s.roll_no, s.name, f.total_fee, f.paid_fee, f.due_fee, f.last_payment_date
            FROM fees f JOIN students s ON f.student_id = s.id
            ORDER BY s.roll_no
            ''',
            fetch=True
        )
        for index, row in enumerate(rows):
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            self.fee_tree.insert('', 'end', values=row, tags=(tag,))

    def load_dashboard(self):
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        total_students = self.db.execute('SELECT COUNT(*) FROM students', fetch=True)[0][0]
        present_today = self.db.execute(
            'SELECT COUNT(*) FROM attendance WHERE date=? AND status="Present"',
            (datetime.now().strftime('%Y-%m-%d'),),
            fetch=True
        )[0][0]
        fee_due = self.db.execute('SELECT COALESCE(SUM(due_fee),0) FROM fees', fetch=True)[0][0]
        avg_marks = self.db.execute(
            'SELECT ROUND(AVG(obtained_marks * 100.0 / max_marks),2) FROM marks',
            fetch=True
        )[0][0]

        cards_data = [
            ('Total Students', total_students, '#0d6efd'),
            ('Present Today', present_today, '#198754'),
            ('Total Fee Due', fee_due, '#fd7e14'),
            ('Average %', avg_marks if avg_marks is not None else 0, '#6f42c1')
        ]

        for title, value, color in cards_data:
            card = tk.Frame(self.stats_frame, bg=color)
            card.pack(side='left', padx=6, pady=4, fill='x', expand=True)
            card.pack_propagate(False)
            tk.Label(card, text=title, bg=color, fg='white',
                     font=('Segoe UI', 10, 'bold')).pack(pady=(10, 0))
            tk.Label(card, text=str(value), bg=color, fg='white',
                     font=('Segoe UI', 16, 'bold')).pack(pady=(2, 10))

        self.dashboard_text.delete('1.0', 'end')
        self.dashboard_text.insert('end', 'System Highlights\n')
        self.dashboard_text.insert('end', '-' * 70 + '\n')
        rows = self.db.execute(
            'SELECT roll_no, name, department, semester FROM students ORDER BY id DESC LIMIT 10',
            fetch=True
        )
        self.dashboard_text.insert('end', 'Latest Students Added:\n')
        for r in rows:
            self.dashboard_text.insert('end', f'Roll: {r[0]} | Name: {r[1]} | Dept: {r[2]} | Sem: {r[3]}\n')

    def load_reports(self):
        self.report_text.delete('1.0', 'end')
        total_students = self.db.execute('SELECT COUNT(*) FROM students', fetch=True)[0][0]
        dept_counts = self.db.execute(
            'SELECT department, COUNT(*) FROM students GROUP BY department ORDER BY COUNT(*) DESC',
            fetch=True
        )
        top_scores = self.db.execute(
            '''
            SELECT s.roll_no, s.name, ROUND(AVG(m.obtained_marks * 100.0 / m.max_marks),2) as avgp
            FROM students s JOIN marks m ON s.id=m.student_id
            GROUP BY s.id ORDER BY avgp DESC LIMIT 5
            ''',
            fetch=True
        )
        fee_dues = self.db.execute(
            '''
            SELECT s.roll_no, s.name, f.due_fee
            FROM fees f JOIN students s ON f.student_id=s.id
            WHERE f.due_fee > 0
            ORDER BY f.due_fee DESC
            ''',
            fetch=True
        )

        self.report_text.insert('end', 'ADVANCED STUDENT MANAGEMENT REPORT\n')
        self.report_text.insert('end', '=' * 80 + '\n')
        self.report_text.insert('end', f'Total Students: {total_students}\n\n')

        self.report_text.insert('end', 'Department Wise Count:\n')
        for d in dept_counts:
            self.report_text.insert('end', f' - {d[0] or "N/A"}: {d[1]}\n')

        self.report_text.insert('end', '\nTop Performing Students:\n')
        for t in top_scores:
            self.report_text.insert('end', f' - {t[0]} | {t[1]} | Average %: {t[2]}\n')

        self.report_text.insert('end', '\nFee Due List:\n')
        if fee_dues:
            for f in fee_dues:
                self.report_text.insert('end', f' - {f[0]} | {f[1]} | Due: {f[2]}\n')
        else:
            self.report_text.insert('end', ' - No pending fee records\n')

    def export_students_csv(self):
        rows = self.db.execute(
            '''
            SELECT roll_no, name, gender, dob, phone, email, course, department, semester, address, created_at
            FROM students ORDER BY id
            ''',
            fetch=True
        )
        if not rows:
            messagebox.showwarning('Warning', 'No data to export')
            return
        path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV File', '*.csv')],
            initialfile='students_export.csv'
        )
        if not path:
            return
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(
                ['Roll No', 'Name', 'Gender', 'DOB', 'Phone', 'Email', 'Course',
                 'Department', 'Semester', 'Address', 'Created At']
            )
            writer.writerows(rows)
        messagebox.showinfo('Exported', f'Data exported to {path}')


if __name__ == '__main__':
    root = tk.Tk()
    db = DatabaseManager()
    LoginWindow(root, db)
    root.mainloop()