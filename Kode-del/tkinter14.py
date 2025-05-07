import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector
import pyotp
import qrcode
from PIL import Image, ImageTk  # pip install pillow hvis ikke installert

##########################################
# Database Manager Klasse
##########################################
class DatabaseManager:
    def __init__(self, config):
        self.config = config

    def execute_query(self, query, params=(), commit=False):
        conn = None
        try:
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor()
            cursor.execute(query, params)
            if commit:
                conn.commit()
                return True
            else:
                return cursor.fetchall()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
            return None
        finally:
            if conn:
                conn.close()

# Global database‐instans
DB_CONFIG = {
    'host': "10.10.25.50",
    'user': "dennis",
    'password': "dennis",
    'database': "Skoleapplikasjon"
}
db_manager = DatabaseManager(DB_CONFIG)

##########################################
# Påloggingsvindu med 2FA
##########################################
class LoginWindow:
    def __init__(self, root):
        self.root = root

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        is_mobile = sw < 800

        if is_mobile:
            root.geometry(f"{sw}x{sh}")
        else:
            root.geometry("300x200")

        root.title("Logg inn")
        root.configure(bg='#f0f8ff')

        base_font = ("Arial", 12 if is_mobile else 10)
        style = ttk.Style()
        style.configure("TLabel", background='#f0f8ff', font=base_font)
        style.configure("TEntry", font=base_font)
        style.configure("TButton", font=base_font)

        ttk.Label(root, text="Brukernavn (epost):").pack(pady=(20,5))
        self.username_entry = ttk.Entry(root, width=40 if is_mobile else 30)
        self.username_entry.pack()

        ttk.Label(root, text="Passord:").pack(pady=(10,5))
        self.password_entry = ttk.Entry(root, width=40 if is_mobile else 30, show="*")
        self.password_entry.pack()

        ttk.Button(root, text="Logg inn", command=self.attempt_login).pack(pady=20)

    def attempt_login(self):
        user = self.username_entry.get().strip()
        pwd  = self.password_entry.get().strip()
        if not user or not pwd:
            messagebox.showwarning("Advarsel", "Fyll ut brukernavn og passord.")
            return

        q = "SELECT rolle_navn, mfa_secret FROM brukere WHERE epost=%s AND passord=%s"
        res = db_manager.execute_query(q, (user, pwd))
        if not res:
            messagebox.showerror("Feil", "Ugyldig brukernavn eller passord.")
            return

        role, secret = res[0]
        if not secret:
            if messagebox.askyesno("2FA ikke aktivert",
                                   "Du har ikke konfigurert 2FA enda.\n\n"
                                   "Vil du konfigurere nå?"):
                new_secret = pyotp.random_base32()
                db_manager.execute_query(
                    "UPDATE brukere SET mfa_secret=%s WHERE epost=%s",
                    (new_secret, user),
                    commit=True
                )
                uri = pyotp.TOTP(new_secret).provisioning_uri(
                    name=user,
                    issuer_name="Skoleapplikasjon"
                )
                qr_img = qrcode.make(uri)
                win = tk.Toplevel(self.root)
                win.title("Konfigurer 2FA")
                win.geometry("300x350")
                ttk.Label(win, text="Skann denne QR-koden\nmed Microsoft Authenticator:",
                          font=("Arial", 12), justify="center").pack(pady=10)
                tk_img = ImageTk.PhotoImage(qr_img)
                lbl = tk.Label(win, image=tk_img)
                lbl.image = tk_img
                lbl.pack(padx=10, pady=10)
                ttk.Button(win, text="Ferdig", command=win.destroy).pack(pady=(0,10))
            return

        code = simpledialog.askstring("2FA",
                                      "Skriv inn 6-sifret kode fra Authenticator:",
                                      parent=self.root)
        if not code or not pyotp.TOTP(secret).verify(code):
            messagebox.showerror("Feil 2FA", "Ugyldig eller utløpt kode.")
            return

        self.root.destroy()
        main_root = tk.Tk()
        SchoolDatabaseApp(main_root, current_user=user, user_role=role)
        main_root.mainloop()

##########################################
# Hoved GUI Applikasjon
##########################################
class SchoolDatabaseApp:
    def __init__(self, root, current_user, user_role):
        self.root = root
        self.current_user = current_user
        self.user_role = user_role.lower()

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        self.is_mobile = sw < 800

        if self.is_mobile:
            root.geometry(f"{sw}x{sh}")
            root.attributes('-fullscreen', True)
        else:
            root.geometry("1400x800")

        root.title(f"Skole DB – {self.current_user} ({self.user_role})")
        root.configure(bg='#f0f8ff')

        self.base_font_size = 14 if self.is_mobile else 10
        self.entry_width = 40 if self.is_mobile else 30
        self.combo_width = 40 if self.is_mobile else 30
        self.pad = 5 if self.is_mobile else 10

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", font=("Arial", self.base_font_size, "bold"), padding=self.pad)
        style.map("TButton", background=[("active", "#2980b9")])
        style.configure("TLabel", background="#f0f8ff", foreground="#2c3e50", font=("Arial", self.base_font_size))
        style.configure("TEntry", font=("Arial", self.base_font_size))
        style.configure("TFrame", background="#f0f8ff")
        style.configure("TLabelFrame", background="#dfe6e9", foreground="#2c3e50",
                        font=("Arial", self.base_font_size, "bold"))
        style.configure("Treeview", font=("Arial", self.base_font_size), fieldbackground="white")
        style.configure("Treeview.Heading", background="#3498db", foreground="white",
                        font=("Arial", self.base_font_size, "bold"))

        self.tables = {
            "admin": {
                "fields": ["epost"],
                "insert_query": "INSERT INTO admin (epost) VALUES (%s)",
                "select_query": "SELECT * FROM admin",
                "foreign_keys": {"epost": {"table": "brukere", "display_fields": ["epost"]}}
            },
            "brukere": {
                "fields": ["fornavn", "etternavn", "rolle_navn", "epost", "passord"],
                "insert_query": "INSERT INTO brukere (fornavn, etternavn, rolle_navn, epost, passord) VALUES (%s, %s, %s, %s, %s)",
                "select_query": "SELECT fornavn, etternavn, rolle_navn, epost, passord FROM brukere",
                "foreign_keys": {"rolle_navn": {"table": "rolle", "display_fields": ["rolle_navn"]}}
            },
            "devices": {
                "fields": ["epost", "device_type", "device_model"],
                "insert_query": "INSERT INTO devices (epost, device_type, device_model) VALUES (%s, %s, %s)",
                "select_query": "SELECT * FROM devices",
                "foreign_keys": {"epost": {"table": "brukere", "display_fields": ["epost"]}}
            },
            "elever": {
                "fields": ["epost", "trinn", "født"],
                "insert_query": "INSERT INTO elever (epost, trinn, født) VALUES (%s, %s, %s)",
                "select_query": "SELECT epost, trinn, født FROM elever",
                "foreign_keys": {
                    "epost": {"table": "brukere", "display_fields": ["epost"]},
                    "trinn": {"table": "klasse", "display_fields": ["trinn"]}
                }
            },
            "elev_fag": {
                "fields": ["epost", "fag_navn", "karakter"],
                "insert_query": "INSERT INTO elev_fag (epost, fag_navn, karakter) VALUES (%s, %s, %s)",
                "select_query": "SELECT * FROM elev_fag",
                "foreign_keys": {
                    "epost": {"table": "brukere", "display_fields": ["epost"]},
                    "fag_navn": {"table": "fag", "display_fields": ["fag_navn"]}
                }
            },
            "fag": {
                "fields": ["fag_navn"],
                "insert_query": "INSERT INTO fag (fag_navn) VALUES (%s)",
                "select_query": "SELECT * FROM fag"
            },
            "fravaer": {
                "fields": ["epost", "dato", "antall_timer"],
                "insert_query": "INSERT INTO fravaer (epost, dato, antall_timer) VALUES (%s, %s, %s)",
                "select_query": "SELECT * FROM fravaer",
                "foreign_keys": {"epost": {"table": "brukere", "display_fields": ["epost"]}}
            },
            "klasse": {
                "fields": ["trinn"],
                "insert_query": "INSERT INTO klasse (trinn) VALUES (%s)",
                "select_query": "SELECT * FROM klasse"
            },
            "klasse_elev": {
                "fields": ["klasse_navn", "epost"],
                "insert_query": "INSERT INTO klasse_elev (klasse_navn, epost) VALUES (%s, %s)",
                "select_query": "SELECT * FROM klasse_elev",
                "foreign_keys": {
                    "klasse_navn": {"table": "klasse", "display_fields": ["klasse_navn"]},
                    "epost": {"table": "brukere", "display_fields": ["epost"]}
                }
            },
            "klasse_laerer": {
                "fields": ["klasse_navn", "epost"],
                "insert_query": "INSERT INTO klasse_laerer (klasse_navn, epost) VALUES (%s, %s)",
                "select_query": "SELECT * FROM klasse_laerer",
                "foreign_keys": {
                    "klasse_navn": {"table": "klasse", "display_fields": ["klasse_navn"]},
                    "epost": {"table": "brukere", "display_fields": ["epost"]}
                }
            },
            "kontroll": {
                "fields": ["epost", "beskrivelse", "dato"],
                "insert_query": "INSERT INTO kontroll (epost, beskrivelse, dato) VALUES (%s, %s, %s)",
                "select_query": "SELECT * FROM kontroll",
                "foreign_keys": {"epost": {"table": "brukere", "display_fields": ["epost"]}}
            },
            "laerer": {
                "fields": ["epost", "fag", "alder"],
                "insert_query": "INSERT INTO laerer (epost, fag, alder) VALUES (%s, %s, %s)",
                "select_query": "SELECT * FROM laerer",
                "foreign_keys": {
                    "epost": {"table": "brukere", "display_fields": ["epost"]},
                    "fag": {"table": "fag", "display_fields": ["fag_navn"]}
                }
            },
            "oppgaver": {
                "fields": ["epost", "oppgave_tekst", "fag_navn"],
                "insert_query": "INSERT INTO oppgaver (epost, oppgave_tekst, fag_navn) VALUES (%s, %s, %s)",
                "select_query": "SELECT * FROM oppgaver",
                "foreign_keys": {
                    "epost": {"table": "brukere", "display_fields": ["epost"]},
                    "fag_navn": {"table": "fag", "display_fields": ["fag_navn"]}
                }
            },
            "postdata": {
                "fields": ["epost", "innhold", "tidspunkt"],
                "insert_query": "INSERT INTO postdata (epost, innhold, tidspunkt) VALUES (%s, %s, %s)",
                "select_query": "SELECT * FROM postdata",
                "foreign_keys": {"epost": {"table": "brukere", "display_fields": ["epost"]}}
            },
            "rolle": {
                "fields": ["rolle_navn"],
                "insert_query": "INSERT INTO rolle (rolle_navn) VALUES (%s)",
                "select_query": "SELECT * FROM rolle"
            },
            "start": {
                "fields": ["innstilling", "verdi"],
                "insert_query": "INSERT INTO start (innstilling, verdi) VALUES (%s, %s)",
                "select_query": "SELECT * FROM start"
            }
        }

        self.create_main_layout()

    def create_main_layout(self):
        # Header
        header = tk.Frame(self.root, bg='#2980b9')
        header.pack(fill=tk.X, pady=(0, self.pad))
        tk.Label(header, text="Skole Database Administrasjon",
                 bg='#2980b9', fg='white',
                 font=("Arial", 24 if self.is_mobile else 20, "bold")
        ).pack(side=tk.LEFT, padx=self.pad)
        tk.Label(header, text=f"Innlogget som: {self.current_user}",
                 bg='#2980b9', fg='white',
                 font=("Arial", self.base_font_size, "italic")
        ).pack(side=tk.RIGHT, padx=self.pad)
        ttk.Button(header, text="Logg ut", command=self.logout).pack(side=tk.RIGHT, padx=self.pad)

        # Meny
        menu = tk.Frame(self.root, bg='#f0f8ff')
        menu.pack(fill=tk.X, pady=self.pad)
        tk.Label(menu, text="Tabell:", bg='#f0f8ff').pack(side=tk.LEFT, padx=(self.pad,0))
        tables = list(self.tables.keys())
        if self.user_role == 'elev':
            tables = [t for t,v in self.tables.items() if 'epost' in v['fields']]
        self.table_var = tk.StringVar()
        self.table_dropdown = ttk.Combobox(menu, textvariable=self.table_var,
                                           values=tables, state="readonly",
                                           width=self.combo_width)
        self.table_dropdown.pack(side=tk.LEFT, padx=self.pad)
        self.table_dropdown.bind("<<ComboboxSelected>>", self.on_table_select)

        tk.Label(menu, text="Søk:", bg='#f0f8ff').pack(side=tk.LEFT, padx=(self.pad,0))
        self.search_entry = tk.Entry(menu, width=self.entry_width,
                                     font=("Arial", self.base_font_size))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=self.pad)
        self.search_entry.bind('<KeyRelease>', self.perform_search)

        tk.Label(menu, text="Sorter etter:", bg='#f0f8ff').pack(side=tk.LEFT, padx=(self.pad,0))
        self.sort_var = tk.StringVar()
        self.sort_combobox = ttk.Combobox(menu, textvariable=self.sort_var,
                                          state="readonly", width=self.combo_width)
        self.sort_combobox.pack(side=tk.LEFT, padx=self.pad)
        ttk.Button(menu, text="Sorter", command=self.sort_results).pack(side=tk.LEFT, padx=self.pad)

        # Desktop vs Mobil layout
        if not self.is_mobile:
            left_panel = tk.Frame(self.root, bg='#f0f8ff')
            left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=self.pad, pady=self.pad)

            if self.user_role != 'elev':
                self.data_entry_frame = ttk.LabelFrame(left_panel, text="Legg til/Endre")
                self.data_entry_frame.pack(fill=tk.X, pady=self.pad)
            else:
                self.data_entry_frame = None
            self.build_data_entry()

            details = ttk.LabelFrame(left_panel, text="Detaljer")
            details.pack(fill=tk.BOTH, expand=True, pady=self.pad)
            self.details_text = tk.Text(details, state='disabled', wrap='word',
                                        font=("Arial", self.base_font_size))
            self.details_text.pack(fill=tk.BOTH, expand=True, padx=self.pad, pady=self.pad)

            right_panel = tk.Frame(self.root, bg='#f0f8ff')
            right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=self.pad, pady=self.pad)
            self.build_results(right_panel)

        else:
            if self.user_role != 'elev':
                self.data_entry_frame = ttk.LabelFrame(self.root, text="Legg til/Endre")
                self.data_entry_frame.pack(fill=tk.X, padx=self.pad, pady=self.pad)
            else:
                self.data_entry_frame = None
            self.build_data_entry()

            details = ttk.LabelFrame(self.root, text="Detaljer")
            details.pack(fill=tk.X, padx=self.pad, pady=self.pad)
            self.details_text = tk.Text(details, height=5, state='disabled', wrap='word',
                                        font=("Arial", self.base_font_size))
            self.details_text.pack(fill=tk.X, padx=self.pad, pady=self.pad)

            self.build_results(self.root)

        # Status‐bar
        self.status_var = tk.StringVar("Velg en tabell for å starte...")
        status = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN,
                          anchor='w', font=("Arial", self.base_font_size),
                          bg='white', fg='#2c3e50')
        status.pack(side=tk.BOTTOM, fill=tk.X)

    def build_data_entry(self):
        if not self.data_entry_frame:
            return
        for w in self.data_entry_frame.winfo_children():
            w.destroy()
        self.entry_widgets = {}
        tbl = self.table_var.get()
        info = self.tables.get(tbl, {})
        fks = info.get('foreign_keys', {})
        for field in info.get('fields', []):
            if tbl=='brukere' and field=='passord' and self.user_role!='admin':
                continue
            frm = tk.Frame(self.data_entry_frame, bg='#dfe6e9')
            frm.pack(fill=tk.X, padx=self.pad, pady=2)
            tk.Label(frm, text=f"{field}:", width=12, anchor='w',
                     bg='#dfe6e9', font=("Arial", self.base_font_size)).pack(side=tk.LEFT)
            if field in fks:
                ref = fks[field]
                ref_info = self.tables[ref['table']]
                data = db_manager.execute_query(ref_info['select_query']) or []
                idxs = [ref_info['fields'].index(df) for df in ref['display_fields']]
                vals = sorted({ " ".join(str(row[i]) for i in idxs) for row in data })
                ent = ttk.Combobox(frm, values=vals, state='readonly',
                                   font=("Arial", self.base_font_size),
                                   width=self.combo_width)
            else:
                ent = tk.Entry(frm, font=("Arial", self.base_font_size),
                               width=self.entry_width)
            ent.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.entry_widgets[field] = ent

    def build_results(self, parent):
        self.results_tree = ttk.Treeview(parent, selectmode='browse')
        self.results_tree.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL,
                                  command=self.results_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscroll=scrollbar.set)
        self.results_tree.bind("<<TreeviewSelect>>", self.on_result_select)

        action_frame = tk.Frame(parent, bg='#f0f8ff')
        action_frame.pack(fill=tk.X, pady=self.pad)
        btns = []
        if self.user_role != 'elev':
            btns = [
                ("Legg til", self.add_record),
                ("Rediger", self.populate_form_for_selected),
                ("Oppdater post", self.update_selected_record),
                ("Oppdater alle", self.update_all_records),
                ("Slett valgte", self.delete_records),
                ("Tøm skjema", self.clear_form)
            ]
        for txt, cmd in btns:
            ttk.Button(action_frame, text=txt, command=cmd).pack(side=tk.LEFT, padx=2)

    def on_table_select(self, event=None):
        self.build_data_entry()
        self.populate_results_tree()
        visible = len(self.tables.get(self.table_var.get(), {}).get('fields', []))
        self.status_var.set(f"Viser data for '{self.table_var.get()}'.")
    
    def populate_results_tree(self):
        tbl = self.table_var.get()
        info = self.tables.get(tbl)
        if not info:
            return
        # clear
        for itm in self.results_tree.get_children():
            self.results_tree.delete(itm)
        all_fields = info['fields']
        if tbl=='brukere' and self.user_role!='admin':
            fields = [f for f in all_fields if f!='passord']
            pass_idx = all_fields.index('passord')
        else:
            fields = all_fields[:]
            pass_idx = None
        self.results_tree['columns'] = tuple(fields)
        self.results_tree.heading('#0', text='')
        self.results_tree.column('#0', width=0, stretch=tk.NO)
        for c in fields:
            self.results_tree.heading(c, text=c)
            self.results_tree.column(c, anchor='center', width=120 if not self.is_mobile else 100)
        # fetch
        rows = db_manager.execute_query(info['select_query']) or []
        if self.user_role=='elev' and 'epost' in all_fields:
            idx = all_fields.index('epost')
            rows = [r for r in rows if r[idx]==self.current_user]
        for r in rows:
            if pass_idx is not None:
                r = tuple(v for i,v in enumerate(r) if i!=pass_idx)
            self.results_tree.insert('', 'end', values=r)
        self.status_var.set(f"{len(rows)} poster funnet i '{tbl}'.")
        self.reselect_first_row()

    def on_result_select(self, event=None):
        sels = self.results_tree.selection()
        self.details_text.configure(state='normal')
        self.details_text.delete('1.0', tk.END)
        if not sels:
            self.details_text.insert(tk.END, "Ingen rad er valgt.")
        else:
            vals = self.results_tree.item(sels[0])['values']
            tbl = self.table_var.get()
            info = self.tables.get(tbl,{})
            all_fields = info.get('fields',[])
            display = [f for f in all_fields if not (tbl=='brukere' and f=='passord' and self.user_role!='admin')]
            for f,v in zip(display, vals):
                self.details_text.insert(tk.END, f"{f}: {v}\n")
        self.details_text.configure(state='disabled')

    def reselect_first_row(self):
        ch = self.results_tree.get_children()
        if ch:
            self.results_tree.selection_set(ch[0])
        else:
            self.details_text.configure(state='normal')
            self.details_text.delete('1.0', tk.END)
            self.details_text.insert(tk.END, "Ingen rad er valgt.")
            self.details_text.configure(state='disabled')
        self.on_result_select()

    def perform_search(self, event=None):
        tbl = self.table_var.get()
        if not tbl: return
        term = self.search_entry.get().lower().strip()
        info = self.tables.get(tbl,{})
        rows = db_manager.execute_query(info['select_query']) or []
        if self.user_role=='elev' and 'epost' in info.get('fields',[]):
            idx = info['fields'].index('epost')
            rows = [r for r in rows if r[idx]==self.current_user]
        matches = [r for r in rows if any(term in str(v).lower() for v in r)]
        # clear then insert
        for itm in self.results_tree.get_children():
            self.results_tree.delete(itm)
        pass_idx = info['fields'].index('passord') if tbl=='brukere' and self.user_role!='admin' else None
        for r in matches:
            row = tuple(v for i,v in enumerate(r) if i!=pass_idx) if pass_idx is not None else r
            self.results_tree.insert('', 'end', values=row)
        self.status_var.set(f"Søket fant {len(matches)} poster.")
        self.reselect_first_row()

    def sort_results(self):
        tbl = self.table_var.get()
        col = self.sort_var.get()
        if not tbl or not col:
            messagebox.showinfo("Sorter", "Velg kolonne.")
            return
        info = self.tables.get(tbl,{})
        q = info['select_query'] + f" ORDER BY {col} ASC"
        rows = db_manager.execute_query(q) or []
        if self.user_role=='elev' and 'epost' in info.get('fields',[]):
            idx = info['fields'].index('epost')
            rows = [r for r in rows if r[idx]==self.current_user]
        for itm in self.results_tree.get_children():
            self.results_tree.delete(itm)
        pass_idx = info['fields'].index('passord') if tbl=='brukere' and self.user_role!='admin' else None
        for r in rows:
            row = tuple(v for i,v in enumerate(r) if i!=pass_idx) if pass_idx is not None else r
            self.results_tree.insert('', 'end', values=row)
        self.status_var.set(f"{len(rows)} poster sortert etter {col}.")
        self.reselect_first_row()

    def add_record(self):
        tbl = self.table_var.get()
        if not tbl:
            messagebox.showwarning("Advarsel", "Velg en tabell først.")
            return
        vals = [w.get().strip() for w in self.entry_widgets.values()]
        if any(v=='' for v in vals):
            messagebox.showwarning("Advarsel", "Alle felt må fylles ut.")
            return
        info = self.tables.get(tbl,{})
        if db_manager.execute_query(info['insert_query'], tuple(vals), commit=True) is None:
            return
        if tbl=='brukere':
            ep = self.entry_widgets['epost'].get().strip()
            secret = pyotp.random_base32()
            db_manager.execute_query(
                "UPDATE brukere SET mfa_secret=%s WHERE epost=%s",
                (secret, ep), commit=True
            )
            uri = pyotp.TOTP(secret).provisioning_uri(name=ep, issuer_name="Skoleapplikasjon")
            qr_img = qrcode.make(uri)
            win = tk.Toplevel(self.root)
            win.title("Konfigurer 2FA")
            win.geometry("300x350")
            ttk.Label(win,
                      text="Skann denne QR-koden\nmed Microsoft Authenticator:",
                      font=("Arial", 12),
                      justify="center").pack(pady=10)
            tk_img = ImageTk.PhotoImage(qr_img)
            lbl = tk.Label(win, image=tk_img)
            lbl.image = tk_img
            lbl.pack(padx=10, pady=10)
            ttk.Button(win, text="Ferdig", command=win.destroy).pack(pady=(0,10))
        messagebox.showinfo("Suksess", "Posten ble lagt til.")
        self.build_data_entry()
        self.populate_results_tree()

    def populate_form_for_selected(self):
        sels = self.results_tree.selection()
        if not sels:
            messagebox.showwarning("Advarsel", "Velg rad først.")
            return
        self.selected_item = sels[0]
        tbl = self.table_var.get()
        info = self.tables.get(tbl,{})
        all_fields = info.get('fields',[])
        vals = self.results_tree.item(self.selected_item)['values']
        # fetch full row for passord etc
        full = db_manager.execute_query(
            info['select_query'] + " WHERE " + " AND ".join(f"{f}=%s" for f in all_fields),
            tuple(vals),) or [[]]
        row = full[0] if full else []
        for i, field in enumerate(all_fields):
            if field in self.entry_widgets:
                w = self.entry_widgets[field]
                w.delete(0, tk.END)
                w.insert(0, str(row[i]))
        self.on_result_select()

    def update_selected_record(self):
        if not hasattr(self, 'selected_item'):
            messagebox.showwarning("Advarsel", "Velg og rediger rad først.")
            return
        tbl = self.table_var.get()
        info = self.tables.get(tbl,{})
        fields = info.get('fields',[])[:]
        new_vals = [self.entry_widgets[f].get().strip() for f in fields if f in self.entry_widgets]
        if any(v=='' for v in new_vals):
            messagebox.showwarning("Advarsel", "Alle felt må fylles ut.")
            return
        old_vals = list(self.results_tree.item(self.selected_item)['values'])
        if tbl=='brukere' and self.user_role!='admin':
            pi = fields.index('passord')
            del fields[pi]
            del old_vals[pi]
        q = f"UPDATE {tbl} SET " + ",".join(f"{f}=%s" for f in fields) + \
            " WHERE " + " AND ".join(f"{f}=%s" for f in fields)
        params = tuple(new_vals + old_vals)
        if db_manager.execute_query(q, params, commit=True) is None:
            return
        messagebox.showinfo("Suksess", "Post oppdatert.")
        self.populate_results_tree()

    def update_all_records(self):
        tbl = self.table_var.get()
        info = self.tables.get(tbl,{})
        fields = info.get('fields',[])
        vals = [self.entry_widgets[f].get().strip() for f in fields if f in self.entry_widgets]
        if any(v=='' for v in vals):
            messagebox.showwarning("Advarsel", "Alle felt må fylles ut.")
            return
        if not messagebox.askyesno("Bekreft", "Oppdater alle poster?"):
            return
        q = f"UPDATE {tbl} SET " + ",".join(f"{f}=%s" for f in fields if f in self.entry_widgets)
        if db_manager.execute_query(q, tuple(vals), commit=True) is None:
            return
        messagebox.showinfo("Suksess", "Alle poster oppdatert.")
        self.populate_results_tree()

    def delete_records(self):
        tbl = self.table_var.get()
        sels = self.results_tree.selection()
        if not tbl or not sels:
            messagebox.showwarning("Advarsel", "Velg tabell og rader.")
            return
        if not messagebox.askyesno("Bekreft", f"Slette {len(sels)} poster?"):
            return
        cols = list(self.results_tree['columns'])
        for s in sels:
            vals = list(self.results_tree.item(s)['values'])
            q = f"DELETE FROM {tbl} WHERE " + " AND ".join(f"{c}=%s" for c in cols)
            if db_manager.execute_query(q, tuple(vals), commit=True) is None:
                return
        messagebox.showinfo("Suksess", f"Slettet {len(sels)} poster.")
        self.populate_results_tree()

    def logout(self):
        self.root.destroy()
        new_root = tk.Tk()
        LoginWindow(new_root)
        new_root.mainloop()

def main():
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
