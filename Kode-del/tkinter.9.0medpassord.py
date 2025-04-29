import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

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

# Globale database-instans
DB_CONFIG = {
    'host': "10.10.25.50",
    'user': "dennis",
    'password': "dennis",
    'database': "Skoleapplikasjon"
}
db_manager = DatabaseManager(DB_CONFIG)

##########################################
# Påloggingsvindu
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
        pwd = self.password_entry.get().strip()
        if not user or not pwd:
            messagebox.showwarning("Advarsel", "Fyll ut brukernavn og passord.")
            return
        q = "SELECT rolle_navn FROM brukere WHERE epost=%s AND passord=%s"
        res = db_manager.execute_query(q, (user, pwd))
        if res:
            role = res[0][0]
            self.root.destroy()
            main_root = tk.Tk()
            app = SchoolDatabaseApp(main_root, current_user=user, user_role=role)
            main_root.mainloop()
        else:
            messagebox.showerror("Feil", "Ugyldig brukernavn eller passord.")

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

        # ttk-stil
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
        # Tabellkonfigurasjon med passord i brukere
        ##########################################
        self.tables = {
            "admin": {
                "fields": ["epost"],
                "insert_query": "INSERT INTO admin (epost) VALUES (%s)",
                "select_query": "SELECT * FROM admin",
                "foreign_keys": {
                    "epost": {"table": "brukere", "display_fields": ["epost"]}
                }
            },
            "brukere": {
                "fields": ["fornavn", "etternavn", "rolle_navn", "epost", "passord"],
                "insert_query": "INSERT INTO brukere (fornavn, etternavn, rolle_navn, epost, passord) VALUES (%s, %s, %s, %s, %s)",
                "select_query": "SELECT fornavn, etternavn, rolle_navn, epost, passord FROM brukere",
                "foreign_keys": {
                    "rolle_navn": {"table": "rolle", "display_fields": ["rolle_navn"]}
                }
            },
            "devices": {
                "fields": ["epost", "device_type", "device_model"],
                "insert_query": "INSERT INTO devices (epost, device_type, device_model) VALUES (%s, %s, %s)",
                "select_query": "SELECT * FROM devices",
                "foreign_keys": {
                    "epost": {"table": "brukere", "display_fields": ["epost"]}
                }
            },
            "elever": {
                "fields": ["epost", "trinn", "fodselsdato"],
                "insert_query": "INSERT INTO elever (epost, trinn, fodselsdato) VALUES (%s, %s, %s)",
                "select_query": "SELECT * FROM elever",
                "foreign_keys": {
                    "epost": {"table": "brukere", "display_fields": ["epost"]},
                    "trinn": {"table": "klasse", "display_fields": ["klasse_navn"]}
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
                "foreign_keys": {
                    "epost": {"table": "brukere", "display_fields": ["epost"]}
                }
            },
            "klasse": {
                "fields": ["klasse_navn"],
                "insert_query": "INSERT INTO klasse (klasse_navn) VALUES (%s)",
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
                "foreign_keys": {
                    "epost": {"table": "brukere", "display_fields": ["epost"]}
                }
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
                "foreign_keys": {
                    "epost": {"table": "brukere", "display_fields": ["epost"]}
                }
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

    def refresh_results(self):
        tbl = self.table_var.get()
        if tbl:
            self.populate_results_tree(tbl)

    ##########################################
    # GUI-oppsett
    ##########################################
    def create_main_layout(self):
        self.main_frame = tk.Frame(self.root, bg='#f0f8ff')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header
        header_frame = tk.Frame(self.main_frame, bg='#2980b9')
        header_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        header_label = tk.Label(header_frame, text="Skole Database Administrasjon",
                                bg='#2980b9', fg='white', font=("Arial", 20, "bold"))
        header_label.pack(side=tk.LEFT, padx=10)

        # Meny for tabellvalg, søk, sortering
        menu_frame = tk.Frame(self.main_frame, bg='#f0f8ff')
        menu_frame.pack(side=tk.TOP, fill=tk.X)
        tk.Label(menu_frame, text="Tabell:", bg='#f0f8ff', font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(5,0))

        tables_to_show = list(self.tables.keys())
        if self.user_role == 'elev':
            tables_to_show = [t for t,v in self.tables.items() if 'epost' in v['fields']]

        self.table_var = tk.StringVar()
        self.table_dropdown = ttk.Combobox(menu_frame, textvariable=self.table_var,
                                           values=tables_to_show, state="readonly", width=30)
        self.table_dropdown.pack(side=tk.LEFT, padx=5)
        self.table_dropdown.bind("<<ComboboxSelected>>", self.on_table_select)

        # Søk
        search_frame = tk.Frame(menu_frame, bg='#f0f8ff')
        search_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Label(search_frame, text="Søk:", bg='#f0f8ff').pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, width=50)
        self.search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.search_entry.bind('<KeyRelease>', self.perform_search)

        # Sortering
        sort_frame = tk.Frame(menu_frame, bg='#f0f8ff')
        sort_frame.pack(side=tk.LEFT, padx=5)
        tk.Label(sort_frame, text="Sorter etter:", bg='#f0f8ff').pack(side=tk.LEFT)
        self.sort_var = tk.StringVar()
        self.sort_combobox = ttk.Combobox(sort_frame, textvariable=self.sort_var,
                                          state="readonly", width=20)
        self.sort_combobox.pack(side=tk.LEFT, padx=5)
        ttk.Button(sort_frame, text="Sorter", command=self.sort_results).pack(side=tk.LEFT)

        # Hovedinnhold
        self.content_frame = tk.Frame(self.main_frame, bg='#f0f8ff')
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.create_data_entry_frame()
        self.create_results_frame()
        self.create_details_frame()
        self.create_status_bar()

    def create_data_entry_frame(self):
        self.data_entry_frame = ttk.LabelFrame(self.content_frame, text="Legg til/Endre")
        self.data_entry_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10), pady=5)
        self.entry_widgets = {}

    def create_results_frame(self):
        self.results_frame = tk.Frame(self.content_frame, bg='#f0f8ff')
        self.results_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)
        self.results_tree = ttk.Treeview(self.results_frame, selectmode='extended')
        self.results_tree.pack(fill=tk.BOTH, expand=True, anchor='w')
        scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscroll=scrollbar.set)
        self.results_tree.bind("<<TreeviewSelect>>", self.on_result_select)

        action_frame = tk.Frame(self.results_frame, bg='#f0f8ff')
        action_frame.pack(fill=tk.X, pady=5)
        self.buttons = []
        for txt, cmd in [
            ("Legg til", self.add_record),
            ("Rediger", self.populate_form_for_selected),
            ("Oppdater post", self.update_selected_record),
            ("Oppdater alle", self.update_all_records),
            ("Slett valgte", self.delete_records),
            ("Tøm skjema", self.clear_form)
        ]:
            btn = ttk.Button(action_frame, text=txt, command=cmd)
            btn.pack(side=tk.LEFT, padx=5)
            self.buttons.append(btn)

        if self.user_role == 'elev':
            for b in self.buttons:
                b.config(state='disabled')

    def create_details_frame(self):
        self.details_frame = ttk.LabelFrame(self.content_frame, text="Detaljer")
        self.details_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10,0), pady=5)
        self.details_text = tk.Text(self.details_frame, height=30, state='disabled',
                                    wrap='word', bg='white')
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("Velg en tabell for å starte...")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1,
                                   relief=tk.SUNKEN, anchor='w',
                                   font=("Arial", 9), bg='white', fg='#2c3e50')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    ##########################################
    # Navigasjon og oppfriskning
    ##########################################
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

    def clear_form(self):
        for w in self.entry_widgets.values():
            w.delete(0, tk.END)
        self.details_text.configure(state='normal')
        self.details_text.delete('1.0', tk.END)
        self.details_text.configure(state='disabled')
        if hasattr(self, 'selected_item'):
            del self.selected_item

    def on_table_select(self, event=None):
        self.clear_form()
        tbl = self.table_var.get()
        info = self.tables.get(tbl)
        if not tbl or not info:
            return
        for w in self.data_entry_frame.winfo_children():
            w.destroy()
        self.entry_widgets = {}
        fks = info.get('foreign_keys', {})
        for field in info['fields']:
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

        self.sort_combobox['values'] = info['fields']
        self.sort_var.set(info['fields'][0])
        self.populate_results_tree(tbl)
        self.status_var.set(f"Viser data for '{tbl}'.")

    def populate_results_tree(self, tbl):
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        cols = tuple(self.tables[tbl]['fields'])
        self.results_tree['columns'] = cols
        self.results_tree.heading('#0', text='')
        self.results_tree.column('#0', width=0, stretch=tk.NO)
        for c in cols:
            self.results_tree.heading(c, text=c)
            self.results_tree.column(c, anchor='center', width=120)

        rows = db_manager.execute_query(self.tables[tbl]['select_query']) or []
        if self.user_role == 'elev' and 'epost' in cols:
            idx = cols.index('epost')
            rows = [r for r in rows if r[idx] == self.current_user]

        for r in rows:
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
            fields = self.tables[self.table_var.get()]['fields']
            for f, v in zip(fields, vals):
                self.details_text.insert(tk.END, f"{f}: {v}\n")
        self.details_text.configure(state='disabled')

    def perform_search(self, event=None):
        tbl = self.table_var.get()
        term = self.search_entry.get().lower().strip()
        if not tbl:
            return
        self.results_tree.delete(*self.results_tree.get_children())
        rows = db_manager.execute_query(self.tables[tbl]['select_query']) or []
        if self.user_role == 'elev' and 'epost' in self.tables[tbl]['fields']:
            idx = self.tables[tbl]['fields'].index('epost')
            rows = [r for r in rows if r[idx] == self.current_user]
        matches = [r for r in rows if any(term in str(val).lower() for val in r)]
        for m in matches:
            self.results_tree.insert('', 'end', values=m)
        self.status_var.set(f"Søket fant {len(matches)} poster.")
        self.reselect_first_row()

    def sort_results(self):
        tbl = self.table_var.get()
        col = self.sort_var.get()
        if not tbl or not col:
            messagebox.showinfo("Sorter", "Velg kolonne.")
            return
        q = self.tables[tbl]['select_query'] + f" ORDER BY {col} ASC"
        rows = db_manager.execute_query(q) or []
        if self.user_role == 'elev' and 'epost' in self.tables[tbl]['fields']:
            idx = self.tables[tbl]['fields'].index('epost')
            rows = [r for r in rows if r[idx] == self.current_user]
        self.results_tree.delete(*self.results_tree.get_children())
        for r in rows:
            self.results_tree.insert('', 'end', values=r)
        self.status_var.set(f"{len(rows)} poster sortert etter {col}.")
        self.reselect_first_row()

    ##########################################
    # CRUD-operasjoner
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
        if db_manager.execute_query(self.tables[tbl]['insert_query'], tuple(vals), commit=True) is None:
            return
        messagebox.showinfo("Suksess", "Posten ble lagt til.")
        self.clear_form()
        self.refresh_results()

    def populate_form_for_selected(self):
        sels = self.results_tree.selection()
        if not sels:
            messagebox.showwarning("Advarsel", "Velg rad først.")
            return
        self.selected_item = sels[0]
        tbl = self.table_var.get()
        fields = self.tables[tbl]['fields']
        vals = self.results_tree.item(self.selected_item)['values']
        for i, f in enumerate(fields):
            w = self.entry_widgets[f]
            w.delete(0, tk.END)
            w.insert(0, str(vals[i]))
        self.update_detail_box()

    def update_detail_box(self):
        self.details_text.configure(state='normal')
        self.details_text.delete('1.0', tk.END)
        for f, w in self.entry_widgets.items():
            self.details_text.insert(tk.END, f"{f}: {w.get()}\n")
        self.details_text.configure(state='disabled')

    def update_selected_record(self):
        tbl = self.table_var.get()
        if not tbl or not hasattr(self, 'selected_item'):
            messagebox.showwarning("Advarsel", "Velg og rediger rad først.")
            return
        fields = self.tables[tbl]['fields']
        new = [self.entry_widgets[f].get().strip() for f in fields]
        if any(v == '' for v in new):
            messagebox.showwarning("Advarsel", "Alle felt må fylles ut.")
            return
        current = self.results_tree.item(self.selected_item)['values']
        pk = self.tables[tbl].get('primary_key', fields)
        vals = new + [current[fields.index(pkf)] for pkf in pk]
        q = f"UPDATE {tbl} SET {','.join(f+'=%s' for f in fields)} WHERE {' AND '.join(pkf+'=%s' for pkf in pk)}"
        if db_manager.execute_query(q, tuple(vals), commit=True) is None:
            return
        messagebox.showinfo("Suksess", "Post oppdatert.")
        self.refresh_results()

    def update_all_records(self):
        tbl = self.table_var.get()
        if not tbl:
            messagebox.showwarning("Advarsel", "Velg tabell først.")
            return
        vals = [w.get().strip() for w in self.entry_widgets.values()]
        if any(v == '' for v in vals):
            messagebox.showwarning("Advarsel", "Alle felt må fylles ut.")
            return
        if not messagebox.askyesno("Bekreft", "Oppdater alle poster?"):
            return
        q = f"UPDATE {tbl} SET {','.join(f+'=%s' for f in self.tables[tbl]['fields'])}"
        if db_manager.execute_query(q, tuple(vals), commit=True) is None:
            return
        messagebox.showinfo("Suksess", "Alle poster oppdatert.")
        self.refresh_results()

    def delete_records(self):
        tbl = self.table_var.get()
        sels = self.results_tree.selection()
        if not tbl or not sels:
            messagebox.showwarning("Advarsel", "Velg tabell og rader.")
            return
        if not messagebox.askyesno("Bekreft", f"Slette {len(sels)} poster?"):
            return
        fields = self.tables[tbl]['fields']
        pk = self.tables[tbl].get('primary_key', fields)
        for s in sels:
            vals = self.results_tree.item(s)['values']
            pkvals = [vals[fields.index(p)] for p in pk]
            q = f"DELETE FROM {tbl} WHERE {' AND '.join(p+'=%s' for p in pk)}"
            if db_manager.execute_query(q, tuple(pkvals), commit=True) is None:
                return
        messagebox.showinfo("Suksess", f"Slettet {len(sels)} poster.")
        self.refresh_results()

##########################################
# Main
##########################################
def main():
    login_root = tk.Tk()
    LoginWindow(login_root)
    login_root.mainloop()

if __name__ == "__main__":
    main()
