import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector
import pyotp
import qrcode
from PIL import Image, ImageTk  # pip install pillow hvis ikke installert
import config

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
                return True,
            else:
                return cursor.fetchall()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
            return None
        finally:
            if conn:
                conn.close()

# Global database‐instans
db_manager = DatabaseManager(config.DB_CONFIG)

##########################################
# Påloggingsvindu med 2FA
##########################################
class LoginWindow:
    def __init__(self, root):
        self.root = root
        root.title("Logg inn")
        root.geometry("300x200")
        root.configure(bg='#f0f8ff')

        ttk.Label(root, text="Brukernavn (epost):", background='#f0f8ff').pack(pady=(20,5))
        self.username_entry = ttk.Entry(root, width=30)
        self.username_entry.pack()

        ttk.Label(root, text="Passord:", background='#f0f8ff').pack(pady=(10,5))
        self.password_entry = ttk.Entry(root, width=30, show="*")
        self.password_entry.pack()

        ttk.Button(root, text="Logg inn", command=self.attempt_login).pack(pady=20)

    def attempt_login(self):
        user = self.username_entry.get().strip()
        pwd  = self.password_entry.get().strip()
        if not user or not pwd:
            messagebox.showwarning("Advarsel", "Fyll ut brukernavn og passord.")
            return

        # Hent rolle og mfa_secret
        q = "SELECT rolle_navn, mfa_secret FROM brukere WHERE epost=%s AND passord=%s"
        res = db_manager.execute_query(q, (user, pwd))
        if not res:
            messagebox.showerror("Feil", "Ugyldig brukernavn eller passord.")
            return

        role, secret = res[0]

        # Hvis 2FA ikke er aktivert
        if not secret:
            if messagebox.askyesno(
                "2FA ikke aktivert",
                "Du har ikke konfigurert 2FA enda.\n\nVil du konfigurere nå?"
            ):
                # Generer hemmelighet og lagre i DB
                new_secret = pyotp.random_base32()
                db_manager.execute_query(
                    "UPDATE brukere SET mfa_secret=%s WHERE epost=%s",
                    (new_secret, user),
                    commit=True
                )

                # Lag provisioning URI og QR-kode
                totp = pyotp.TOTP(new_secret)
                uri = totp.provisioning_uri(
                    name=user,
                    issuer_name="Skoleapplikasjon"
                )
                qr_img = qrcode.make(uri)

                # Vis QR-kode i eget vindu
                win = tk.Toplevel(self.root)
                win.title("Konfigurer 2FA")
                win.geometry("300x350")
                tk.Label(
                    win,
                    text="Skann denne QR-koden\nmed Microsoft Authenticator:",
                    font=("Arial", 12),
                    justify="center"
                ).pack(pady=10)
                tk_img = ImageTk.PhotoImage(qr_img)
                lbl = tk.Label(win, image=tk_img)
                lbl.image = tk_img  # behold referanse
                lbl.pack(padx=10, pady=10)
                ttk.Button(win, text="Ferdig", command=win.destroy).pack(pady=(0,10))
            return

        # Spør om koden fra Authenticator og verifiser
        code = simpledialog.askstring(
            "2FA",
            "Skriv inn 6-sifret kode fra Authenticator:",
            parent=self.root
        )
        if not code or not pyotp.TOTP(secret).verify(code):
            messagebox.showerror("Feil 2FA", "Ugyldig eller utløpt kode.")
            return

        # Alt OK → åpne hovedapplikasjon
        self.root.destroy()
        main_root = tk.Tk()
        app = SchoolDatabaseApp(main_root, current_user=user, user_role=role)
        main_root.mainloop()

##########################################
# Hoved GUI Applikasjon
##########################################
class SchoolDatabaseApp:
    def __init__(self, root, current_user, user_role):
        self.root = root
        self.current_user = current_user
        self.user_role = user_role.lower()  # 'admin', 'laerer' eller 'elev'

        self.root.title(f"Skole DB – {self.current_user} ({self.user_role})")
        self.root.geometry("1400x800")
        self.root.configure(bg='#f0f8ff')

        # Konfigurer ttk‐stil
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", font=("Arial", 10, "bold"), background="#3498db",
                        foreground="white", borderwidth=0)
        style.map("TButton", background=[("active", "#2980b9")])
        style.configure("TLabel", background="#f0f8ff", foreground="#2c3e50", font=("Arial", 10))
        style.configure("TEntry", font=("Arial", 10))
        style.configure("TFrame", background="#f0f8ff")
        style.configure("TLabelFrame", background="#dfe6e9", foreground="#2c3e50", font=("Arial", 10, "bold"))
        style.configure("Treeview", background="white", foreground="#2c3e50", font=("Arial", 10), fieldbackground="white")
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#3498db", foreground="white")

        ##########################################
        # Tabellkonfigurasjon
        ##########################################
        self.tables = {
            "brukere": {
                "fields": ["fornavn", "etternavn", "rolle_navn", "epost", "passord"],
                "insert_query": "INSERT INTO brukere (fornavn, etternavn, rolle_navn, epost, passord) VALUES (%s, %s, %s, %s, %s)",
                "select_query": "SELECT fornavn, etternavn, rolle_navn, epost, passord FROM brukere",
                "foreign_keys": {"rolle_navn": {"table": "rolle", "display_fields": ["rolle_navn"]}}
            },
            "elever": {
                "fields": ["epost", "trinn", "født"],
                "insert_query": "INSERT INTO elever (epost, trinn, født) VALUES (%s, %s, %s)",
                # Endret her:
                "select_query": """
                SELECT e.epost, e.trinn, e.født
                FROM elever e
                JOIN brukere b ON e.epost = b.epost
                WHERE b.rolle_navn = 'elev'
        """,
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
            "klasse": {
                "fields": ["trinn"],
                "insert_query": "INSERT INTO klasse (trinn) VALUES (%s)",
                "select_query": "SELECT * FROM klasse"
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
            }
        }

        self.create_main_layout()

    ##########################################
    # GUI-oppsett
    ##########################################
    def create_main_layout(self):
        # Hovedramme
        self.main_frame = tk.Frame(self.root, bg='#f0f8ff')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header med tittel, innlogget-etikett og Logg ut-knapp
        header = tk.Frame(self.main_frame, bg='#2980b9')
        header.pack(fill=tk.X, pady=(0,10))
        tk.Label(header, text="Skole Database Administrasjon",
                 bg='#2980b9', fg='white', font=("Arial",20,"bold")).pack(side=tk.LEFT, padx=10)
        tk.Label(header, text=f"Innlogget som: {self.current_user}",
                 bg='#2980b9', fg='white', font=("Arial",10,"italic")).pack(side=tk.RIGHT, padx=10)
        ttk.Button(header, text="Logg ut", command=self.logout).pack(side=tk.RIGHT, padx=10)

        # Meny (tabellvalg, søk, sort)
        menu = tk.Frame(self.main_frame, bg='#f0f8ff')
        menu.pack(fill=tk.X)
        tk.Label(menu, text="Tabell:", bg='#f0f8ff', font=("Arial",10,"bold")).pack(side=tk.LEFT, padx=(5,0))
        tables_to_show = list(self.tables.keys())
        if self.user_role == 'elev':
            tables_to_show = [t for t,v in self.tables.items() if 'epost' in v['fields']]
        self.table_var = tk.StringVar()
        self.table_dropdown = ttk.Combobox(menu, textvariable=self.table_var,
                                           values=tables_to_show, state="readonly", width=30)
        self.table_dropdown.pack(side=tk.LEFT, padx=5)
        self.table_dropdown.bind("<<ComboboxSelected>>", self.on_table_select)

        # Søk
        search_frame = tk.Frame(menu, bg='#f0f8ff')
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Label(search_frame, text="Søk:", bg='#f0f8ff').pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, width=50)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind('<KeyRelease>', self.perform_search)

        # Sorter
        sort_frame = tk.Frame(menu, bg='#f0f8ff')
        sort_frame.pack(side=tk.LEFT, padx=5)
        tk.Label(sort_frame, text="Sorter etter:", bg='#f0f8ff').pack(side=tk.LEFT)
        self.sort_var = tk.StringVar()
        self.sort_combobox = ttk.Combobox(sort_frame, textvariable=self.sort_var,
                                          state="readonly", width=20)
        self.sort_combobox.pack(side=tk.LEFT, padx=5)
        ttk.Button(sort_frame, text="Sorter", command=self.sort_results).pack(side=tk.LEFT)

        # Data‐entry‐panel kun for admin og lærere
        if self.user_role != 'elev':
            self.data_entry_frame = ttk.LabelFrame(self.main_frame, text="Legg til/Endre")
            self.data_entry_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10), pady=5)
            self.entry_widgets = {}
        else:
            self.data_entry_frame = None
            self.entry_widgets = {}

            

        # Resultater
        self.results_frame = tk.Frame(self.main_frame, bg='#f0f8ff')
        self.results_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)
        self.results_tree = ttk.Treeview(self.results_frame, selectmode='browse')
        self.results_tree.pack(fill=tk.BOTH, expand=True, anchor='w')
        scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL,
                                  command=self.results_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscroll=scrollbar.set)
        self.results_tree.bind("<<TreeviewSelect>>", self.on_result_select)

        # CRUD‐knapper kun for admin og lærere
        action_frame = tk.Frame(self.results_frame, bg='#f0f8ff')
        action_frame.pack(fill=tk.X, pady=5)
        if self.user_role != 'elev':
            for txt, cmd in [
                ("Legg til", self.add_record),
                ("Rediger", self.populate_form_for_selected),
                ("Oppdater post", self.update_selected_record),
                ("Oppdater alle", self.update_all_records),
                ("Slett valgte", self.delete_records),
                ("Tøm skjema", self.clear_form)
            ]:
                ttk.Button(action_frame, text=txt, command=cmd).pack(side=tk.LEFT, padx=5)

        # Detaljer‐panel
        details = ttk.LabelFrame(self.main_frame, text="Detaljer")
        details.pack(side=tk.RIGHT, fill=tk.Y, padx=(10,0), pady=5)
        self.details_text = tk.Text(details, height=30, state='disabled', wrap='word', bg='white')
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Status‐bar
        self.status_var = tk.StringVar(value="Velg en tabell for å starte...")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1,
                                   relief=tk.SUNKEN, anchor='w',
                                   font=("Arial",9), bg='white', fg='#2c3e50')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    ##########################################
    # Logg ut-funksjon
    ##########################################
    def logout(self):
        self.root.destroy()
        new_root = tk.Tk()
        LoginWindow(new_root)
        new_root.mainloop()

    ##########################################
    # Navigasjon og oppfriskning
    ##########################################
    def clear_form(self):
        for w in self.entry_widgets.values():
            w.delete(0, tk.END)
        self.details_text.configure(state='normal')
        self.details_text.delete('1.0', tk.END)
        self.details_text.configure(state='disabled')
        if hasattr(self, 'selected_item'):
            del self.selected_item

    def reselect_first_row(self):
        children = self.results_tree.get_children()
        if children:
            self.results_tree.selection_set(children[0])
        else:
            self.details_text.configure(state='normal')
            self.details_text.delete('1.0', tk.END)
            self.details_text.insert(tk.END, "Ingen rad er valgt.")
            self.details_text.configure(state='disabled')
        self.on_result_select()

    ##########################################
    # Tabellvalg og visning
    ##########################################
    def on_table_select(self, event=None):
        tbl = self.table_var.get()
        info = self.tables.get(tbl)
        if not tbl or not info:
            return

        self.clear_form()

        # Bygg data‐entry‐skjema hvis tillatt
        if self.data_entry_frame is not None:
            for w in self.data_entry_frame.winfo_children():
                w.destroy()
            self.entry_widgets = {}
            fks = info.get('foreign_keys', {})
            for field in info['fields']:
                if tbl == 'brukere' and field == 'passord' and self.user_role != 'admin':
                    continue
                frm = tk.Frame(self.data_entry_frame, bg='#dfe6e9')
                frm.pack(fill=tk.X, padx=5, pady=3)
                tk.Label(frm, text=f"{field}:", width=15, anchor='w',
                         bg='#dfe6e9', font=("Arial",10)).pack(side=tk.LEFT)
                if field in fks:
                    ref = fks[field]
                    ref_info = self.tables[ref['table']]
                    data = db_manager.execute_query(ref_info['select_query']) or []
                    idxs = [ref_info['fields'].index(df) for df in ref['display_fields']]
                    seen, vals = set(), []
                    for row in data:
                        txt = " ".join(str(row[i]) for i in idxs)
                        if txt not in seen:
                            seen.add(txt)
                            vals.append(txt)
                    ent = ttk.Combobox(frm, values=vals, state='readonly', font=("Arial",10))
                else:
                    ent = tk.Entry(frm, font=("Arial",10))
                ent.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.entry_widgets[field] = ent

        visible_fields = [
            f for f in info['fields']
            if not (tbl == 'brukere' and f == 'passord' and self.user_role != 'admin')
        ]
        self.sort_combobox['values'] = visible_fields
        if visible_fields:
            self.sort_var.set(visible_fields[0])

        self.populate_results_tree(tbl)
        self.status_var.set(f"Viser data for '{tbl}'.")

    def populate_results_tree(self, tbl):
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        info = self.tables[tbl]
        all_fields = info['fields']
        if tbl == 'brukere' and self.user_role != 'admin':
            fields = [f for f in all_fields if f != 'passord']
            pass_idx = all_fields.index('passord')
        else:
            fields = list(all_fields)
            pass_idx = None

        self.results_tree['columns'] = tuple(fields)
        self.results_tree.heading('#0', text='')
        self.results_tree.column('#0', width=0, stretch=tk.NO)
        for c in fields:
            self.results_tree.heading(c, text=c)
            self.results_tree.column(c, anchor='center', width=120)

        rows = db_manager.execute_query(info['select_query']) or []
        if self.user_role == 'elev' and 'epost' in all_fields:
            epost_idx = all_fields.index('epost')
            rows = [r for r in rows if r[epost_idx] == self.current_user]

        for r in rows:
            if pass_idx is not None:
                r = tuple(v for i,v in enumerate(r) if i != pass_idx)
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
            info = self.tables[tbl]
            all_fields = info['fields']
            display_fields = [
                f for f in all_fields
                if not (tbl == 'brukere' and f == 'passord' and self.user_role != 'admin')
            ]
            for f,v in zip(display_fields, vals):
                self.details_text.insert(tk.END, f"{f}: {v}\n")
        self.details_text.configure(state='disabled')

    ##########################################
    # Søk og sortering
    ##########################################
    def perform_search(self, event=None):
        tbl = self.table_var.get()
        if not tbl:
            return
        term = self.search_entry.get().lower().strip()
        self.results_tree.delete(*self.results_tree.get_children())
        info = self.tables[tbl]
        rows = db_manager.execute_query(info['select_query']) or []
        if self.user_role == 'elev' and 'epost' in info['fields']:
            idx = info['fields'].index('epost')
            rows = [r for r in rows if r[idx] == self.current_user]
        matches = [r for r in rows if any(term in str(v).lower() for v in r)]
        pass_idx = info['fields'].index('passord') if tbl=='brukere' and self.user_role!='admin' else None
        for r in matches:
            row = tuple(v for i,v in enumerate(r) if i != pass_idx) if pass_idx is not None else r
            self.results_tree.insert('', 'end', values=row)
        self.status_var.set(f"Søket fant {len(matches)} poster.")
        self.reselect_first_row()

    def sort_results(self):
        tbl = self.table_var.get()
        col = self.sort_var.get()
        if not tbl or not col:
            messagebox.showinfo("Sorter", "Velg kolonne.")
            return
        info = self.tables[tbl]
        q = info['select_query'] + f" ORDER BY {col} ASC"
        rows = db_manager.execute_query(q) or []
        if self.user_role == 'elev' and 'epost' in info['fields']:
            idx = info['fields'].index('epost')
            rows = [r for r in rows if r[idx] == self.current_user]
        pass_idx = info['fields'].index('passord') if tbl=='brukere' and self.user_role!='admin' else None
        self.results_tree.delete(*self.results_tree.get_children())
        for r in rows:
            row = tuple(v for i,v in enumerate(r) if i != pass_idx) if pass_idx is not None else r
            self.results_tree.insert('', 'end', values=row)
        self.status_var.set(f"{len(rows)} poster sortert etter {col}.")
        self.reselect_first_row()

    ##########################################
    # CRUD‐operasjoner (kun admin/lærere)
    ##########################################
    def add_record(self):
        tbl = self.table_var.get()
        if not tbl:
            messagebox.showwarning("Advarsel", "Velg en tabell først.")
            return
        vals = [w.get().strip() for w in self.entry_widgets.values()]
        if any(v == '' for v in vals):
            messagebox.showwarning("Advarsel", "Alle felt må fylles ut.")
            return
        info = self.tables[tbl]
        if db_manager.execute_query(info['insert_query'], tuple(vals), commit=True) is None:
            return
        if tbl == 'brukere':
            ep = self.entry_widgets['epost'].get().strip()
            secret = pyotp.random_base32()
            db_manager.execute_query(
                "UPDATE brukere SET mfa_secret=%s WHERE epost=%s",
                (secret, ep), commit=True
            )
            totp = pyotp.TOTP(secret)
            uri = totp.provisioning_uri(name=ep, issuer_name="Skoleapplikasjon")
            qr_img = qrcode.make(uri)
            win = tk.Toplevel(self.root)
            win.title("Konfigurer 2FA")
            win.geometry("300x350")
            tk.Label(win, text="Skann denne QR-koden\nmed Microsoft Authenticator:",
                     font=("Arial", 12), justify="center").pack(pady=10)
            tk_img = ImageTk.PhotoImage(qr_img)
            lbl = tk.Label(win, image=tk_img)
            lbl.image = tk_img
            lbl.pack(padx=10, pady=10)
            ttk.Button(win, text="Ferdig", command=win.destroy).pack(pady=(0,10))
        messagebox.showinfo("Suksess", "Posten ble lagt til.")
        self.clear_form()
        self.populate_results_tree(tbl)

    def populate_form_for_selected(self):
        sels = self.results_tree.selection()
        if not sels:
            messagebox.showwarning("Advarsel", "Velg rad først.")
            return
        self.selected_item = sels[0]
        tbl = self.table_var.get()
        info = self.tables[tbl]
        all_fields = info['fields']
        full_row = db_manager.execute_query(
            info['select_query'] + " WHERE " + " AND ".join(f"{f}=%s" for f in all_fields),
            tuple(self.results_tree.item(self.selected_item)['values']),
        ) or [[]]
        full_row = full_row[0] if full_row else []
        for i, field in enumerate(all_fields):
            if field in self.entry_widgets:
                widget = self.entry_widgets[field]
                widget.delete(0, tk.END)
                widget.insert(0, str(full_row[i]))
        self.on_result_select()

    def update_selected_record(self):
        tbl = self.table_var.get()
        if not hasattr(self, 'selected_item') or not tbl:
            messagebox.showwarning("Advarsel", "Velg og rediger rad først.")
            return
        info = self.tables[tbl]
        fields = info['fields'].copy()
        new_vals = [self.entry_widgets[f].get().strip() for f in fields if f in self.entry_widgets]
        if any(v == '' for v in new_vals):
            messagebox.showwarning("Advarsel", "Alle felt må fylles ut.")
            return
        old_vals = list(self.results_tree.item(self.selected_item)['values'])
        if tbl=='brukere' and self.user_role!='admin':
            pass_idx = fields.index('passord')
            del fields[pass_idx]
            del old_vals[pass_idx]
        q = f"UPDATE {tbl} SET " + ",".join(f"{f}=%s" for f in fields) + \
            " WHERE " + " AND ".join(f"{f}=%s" for f in fields)
        params = tuple(new_vals + old_vals)
        if db_manager.execute_query(q, params, commit=True) is None:
            return
        messagebox.showinfo("Suksess", "Post oppdatert.")
        self.populate_results_tree(tbl)

    def update_all_records(self):
        tbl = self.table_var.get()
        if not tbl:
            messagebox.showwarning("Advarsel", "Velg tabell først.")
            return
        info = self.tables[tbl]
        fields = info['fields']
        vals = [self.entry_widgets[f].get().strip() for f in fields if f in self.entry_widgets]
        if any(v == '' for v in vals):
            messagebox.showwarning("Advarsel", "Alle felt må fylles ut.")
            return
        if not messagebox.askyesno("Bekreft", "Oppdater alle poster?"):
            return
        q = f"UPDATE {tbl} SET " + ",".join(f"{f}=%s" for f in fields if f in self.entry_widgets)
        if db_manager.execute_query(q, tuple(vals), commit=True) is None:
            return
        messagebox.showinfo("Suksess", "Alle poster oppdatert.")
        self.populate_results_tree(tbl)

    def delete_records(self):
        tbl = self.table_var.get()
        sels = self.results_tree.selection()
        if not tbl or not sels:
            messagebox.showwarning("Advarsel", "Velg tabell og rader.")
            return
        if not messagebox.askyesno("Bekreft", f"Slette {len(sels)} poster?"):
            return
        fields = list(self.results_tree["columns"])
        for s in sels:
            vals = list(self.results_tree.item(s)["values"])
            q = f"DELETE FROM {tbl} WHERE " + " AND ".join(f"{f}=%s" for f in fields)
            if db_manager.execute_query(q, tuple(vals), commit=True) is None:
                return
        messagebox.showinfo("Suksess", f"Slettet {len(sels)} poster.")
        self.populate_results_tree(tbl)

##########################################
# Main
##########################################
def main():
    login_root = tk.Tk()
    LoginWindow(login_root)
    login_root.mainloop()

if __name__ == "__main__":
    main()
