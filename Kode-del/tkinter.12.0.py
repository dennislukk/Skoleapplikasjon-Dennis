import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
import pyotp
import qrcode
from io import BytesIO
from PIL import Image, ImageTk

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

# Global database-instans
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
        pwd  = self.password_entry.get().strip()
        if not user or not pwd:
            messagebox.showwarning("Advarsel", "Fyll ut brukernavn og passord.")
            return

        # Sjekk brukernavn/passord
        q = "SELECT rolle_navn, mfa_secret FROM brukere WHERE epost=%s AND passord=%s"
        res = db_manager.execute_query(q, (user, pwd))
        if not res:
            messagebox.showerror("Feil", "Ugyldig brukernavn eller passord.")
            return

        role, secret = res[0]
        self.root.withdraw()  # Skjul login-vindu

        if not secret:
            # Første gang: opprett ny hemmelighet
            secret = pyotp.random_base32()
            upd = "UPDATE brukere SET mfa_secret=%s WHERE epost=%s"
            db_manager.execute_query(upd, (secret, user), commit=True)
            MFASetupWindow(self.root, user, role, secret)
        else:
            # Har allerede satt opp: gå rett til kode-verifisering
            MFAVerifyWindow(self.root, user, role, secret)

##########################################
# MFA Setup-vindu (QR-kode)
##########################################
class MFASetupWindow:
    def __init__(self, parent, user, role, secret):
        self.parent = parent
        self.user = user
        self.role = role
        self.secret = secret

        self.win = tk.Toplevel(parent)
        self.win.title("Sett opp MFA")
        self.win.geometry("350x500")

        issuer = "SkoleApp"
        uri = pyotp.totp.TOTP(self.secret).provisioning_uri(self.user, issuer_name=issuer)

        # Generer QR-kode
        qr = qrcode.make(uri)
        bio = BytesIO()
        qr.save(bio, format="PNG")
        img = Image.open(bio)
        self.tkimg = ImageTk.PhotoImage(img.resize((300,300)))

        tk.Label(self.win, text="Skann QR-koden i Microsoft Authenticator:").pack(pady=10)
        tk.Label(self.win, image=self.tkimg).pack()
        tk.Label(self.win, text="Deretter, tast inn koden:").pack(pady=(20,5))

        self.code_entry = ttk.Entry(self.win, width=20)
        self.code_entry.pack()

        ttk.Button(self.win, text="Bekreft kode", command=self.verify_code).pack(pady=(20,5))

        # Fortsett-knapp, deaktivert inntil kode er verifisert
        self.proceed_button = ttk.Button(self.win, text="Fortsett", command=self.proceed, state=tk.DISABLED)
        self.proceed_button.pack(pady=10)

    def verify_code(self):
        code = self.code_entry.get().strip()
        totp = pyotp.TOTP(self.secret)
        if totp.verify(code):
            messagebox.showinfo("Suksess", "Kode verifisert! Klikk Fortsett for å gå videre.")
            self.proceed_button['state'] = tk.NORMAL
        else:
            messagebox.showerror("Feil", "Ugyldig kode – prøv igjen.")

    def proceed(self):
        self.win.destroy()
        main_root = tk.Tk()
        SchoolDatabaseApp(main_root, current_user=self.user, user_role=self.role)
        main_root.mainloop()

##########################################
# MFA Verify-vindu (etter oppsett)
##########################################
class MFAVerifyWindow:
    def __init__(self, parent, user, role, secret):
        self.parent = parent
        self.user = user
        self.role = role
        self.secret = secret

        self.win = tk.Toplevel(parent)
        self.win.title("To-faktor pålogging")
        self.win.geometry("300x300")

        ttk.Label(self.win, text="Tast inn kode fra Authenticator:").pack(pady=(40,10))
        self.code_entry = ttk.Entry(self.win, width=20)
        self.code_entry.pack()

        ttk.Button(self.win, text="Logg inn", command=self.verify_code).pack(pady=(20,5))

        # Fortsett-knapp, deaktivert inntil kode er verifisert
        self.proceed_button = ttk.Button(self.win, text="Fortsett", command=self.proceed, state=tk.DISABLED)
        self.proceed_button.pack(pady=10)

    def verify_code(self):
        code = self.code_entry.get().strip()
        totp = pyotp.TOTP(self.secret)
        if totp.verify(code):
            messagebox.showinfo("Suksess", "Kode verifisert! Klikk Fortsett for å gå videre.")
            self.proceed_button['state'] = tk.NORMAL
        else:
            messagebox.showerror("Feil", "Ugyldig kode – prøv igjen.")

    def proceed(self):
        self.win.destroy()
        main_root = tk.Tk()
        SchoolDatabaseApp(main_root, current_user=self.user, user_role=self.role)
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

        # Konfigurer ttk-stil
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
            "admin": {
                "fields": ["epost"],
                "insert_query": "INSERT INTO admin (epost) VALUES (%s)",
                "select_query": "SELECT * FROM admin",
                "foreign_keys": {"epost": {"table": "brukere", "display_fields": ["epost"]}}
            },
            "brukere": {
                "fields": ["fornavn", "etternavn", "rolle_navn", "epost", "passord", "mfa_secret"],
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
                "foreign_keys": {"epost": {"table": "brukere", "display_fields": ["epost"]},
                                  "trinn": {"table": "klasse", "display_fields": ["trinn"]}}
            },
            "elev_fag": {
                "fields": ["epost", "fag_navn", "karakter"],
                "insert_query": "INSERT INTO elev_fag (epost, fag_navn, karakter) VALUES (%s, %s, %s)",
                "select_query": "SELECT * FROM elev_fag",
                "foreign_keys": {"epost": {"table": "brukere", "display_fields": ["epost"]},
                                  "fag_navn": {"table": "fag", "display_fields": ["fag_navn"]}}
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
                "foreign_keys": {"klasse_navn": {"table": "klasse", "display_fields": ["klasse_navn"]},
                                  "epost": {"table": "brukere", "display_fields": ["epost"]}}
            },
            "klasse_laerer": {
                "fields": ["klasse_navn", "epost"],
                "insert_query": "INSERT INTO klasse_laerer (klasse_navn, epost) VALUES (%s, %s)",
                "select_query": "SELECT * FROM klasse_laerer",
                "foreign_keys": {"klasse_navn": {"table": "klasse", "display_fields": ["klasse_navn"]},
                                  "epost": {"table": "brukere", "display_fields": ["epost"]}}
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
                "foreign_keys": {"epost": {"table": "brukere", "display_fields": ["epost"]},
                                  "fag": {"table": "fag", "display_fields": ["fag_navn"]}}
            },
            "oppgaver": {
                "fields": ["epost", "oppgave_tekst", "fag_navn"],
                "insert_query": "INSERT INTO oppgaver (epost, oppgave_tekst, fag_navn) VALUES (%s, %s, %s)",
                "select_query": "SELECT * FROM oppgaver",
                "foreign_keys": {"epost": {"table": "brukere", "display_fields": ["epost"]},
                                  "fag_navn": {"table": "fag", "display_fields": ["fag_navn"]}}
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

    ##########################################
    # GUI-oppsett
    ##########################################
    def create_main_layout(self):
        # Hovedramme
        self.main_frame = tk.Frame(self.root, bg='#f0f8ff')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header
        header = tk.Frame(self.main_frame, bg='#2980b9')
        header.pack(fill=tk.X, pady=(0,10))
        tk.Label(header, text="Skole Database Administrasjon",
                 bg='#2980b9', fg='white', font=("Arial",20,"bold")).pack(side=tk.LEFT, padx=10)

        # Meny (tabellvalg, søk, sort)
        menu = tk.Frame(self.main_frame, bg='#f0f8ff')
        menu.pack(fill=tk.X)

        tk.Label(menu, text="Tabell:", bg='#f0f8ff', font=("Arial",10,"bold")).pack(side=tk.LEFT, padx=(5,0))
        # Hvilke tabeller kan elev se?
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
        scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscroll=scrollbar.set)
        self.results_tree.bind("<<TreeviewSelect>>", self.on_result_select)

        # CRUD‐knapper kun for admin og lærere
        action_frame = tk.Frame(self.results_frame, bg='#f0f8ff')
        action_frame.pack(fill=tk.X, pady=5)
        self.buttons = []
        if self.user_role != 'elev':
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
                # Skjul passord for ikke-admin
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

        # Oppdater sorteringsvalg (uten passord for ikke-admin)
        visible_fields = [
            f for f in info['fields']
            if not (tbl == 'brukere' and f == 'passord' and self.user_role != 'admin')
        ]
        self.sort_combobox['values'] = visible_fields
        if visible_fields:
            self.sort_var.set(visible_fields[0])

        self.populate_results_tree(tbl)
        self.status_var.set(f"Viser data for '{tbl}'.")

    def populate_results_tree(self, tbl):  # … resten uendret …
        # (samme som før)
        pass

    # … (alle andre metoder for søk, sort, CRUD) …
    # Kopier resten av metodene fra din opprinnelige kode uten endringer.

# Main
def main():
    login_root = tk.Tk()
    LoginWindow(login_root)
    login_root.mainloop()

if __name__ == "__main__":
    main()
