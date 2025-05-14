```python
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
                    (new_secret, user), commit=True
                )
                uri = pyotp.TOTP(new_secret).provisioning_uri(name=user, issuer_name="Skoleapplikasjon")
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
        self.entry_width    = 40 if self.is_mobile else 30
        self.combo_width    = 40 if self.is_mobile else 30
        self.pad            = 5  if self.is_mobile else 10

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", font=("Arial", self.base_font_size, "bold"), padding=self.pad)
        style.map("TButton", background=[("active", "#2980b9")])
        style.configure("TLabel", background="#f0f8ff", foreground="#2c3e50", font=("Arial", self.base_font_size))
        style.configure("TEntry", font=("Arial", self.base_font_size))
        style.configure("TFrame", background="#f0f8ff")
        style.configure("TLabelFrame", background="#dfe6e9", foreground="#2c3e50", font=("Arial", self.base_font_size, "bold"))
        style.configure("Treeview", font=("Arial", self.base_font_size), fieldbackground="white")
        style.configure("Treeview.Heading", background="#3498db", foreground="white", font=("Arial", self.base_font_size, "bold"))

        self.tables = {
            "admin": {
                "fields": ["epost"],
                "insert_query": "INSERT INTO admin (epost) VALUES (%s)",
                "select_query": "SELECT * FROM admin",
                "foreign_keys": {"epost": {"table": "brukere", "display_fields": ["epost"]}}
            },
            "brukere": {
                "fields": ["fornavn","etternavn","rolle_navn","epost","passord"],
                "insert_query": "INSERT INTO brukere (fornavn,etternavn,rolle_navn,epost,passord) VALUES (%s,%s,%s,%s,%s)",
                "select_query": "SELECT fornavn,etternavn,rolle_navn,epost,passord FROM brukere",
                "foreign_keys": {"rolle_navn": {"table":"rolle","display_fields":["rolle_navn"]}}
            },
            # legg til resten av tabellene på samme måte...
        }

        self.create_main_layout()

    def create_main_layout(self):
        # Header
        header = tk.Frame(self.root, bg='#2980b9')
        header.pack(fill=tk.X, pady=(0,self.pad))
        tk.Label(header, text="Skole Database Administrasjon", bg='#2980b9', fg='white', font=("Arial",24 if self.is_mobile else 20,"bold")).pack(side=tk.LEFT, padx=self.pad)
        tk.Label(header, text=f"Innlogget som: {self.current_user}", bg='#2980b9', fg='white', font=("Arial",self.base_font_size,"italic")).pack(side=tk.RIGHT, padx=self.pad)
        ttk.Button(header, text="Logg ut", command=self.logout).pack(side=tk.RIGHT, padx=self.pad)

        # Meny: Tabellvalg, Søk, Sort
        menu = tk.Frame(self.root, bg='#f0f8ff')
        menu.pack(fill=tk.X, pady=self.pad)
        tk.Label(menu, text="Tabell:", bg='#f0f8ff').pack(side=tk.LEFT, padx=(self.pad,0))
        tables = list(self.tables.keys())
        if self.user_role=='elev':
            tables=[t for t,v in self.tables.items() if 'epost' in v['fields']]
        self.table_var = tk.StringVar()
        self.table_dropdown = ttk.Combobox(menu, textvariable=self.table_var, values=tables, state="readonly", width=self.combo_width)
        self.table_dropdown.pack(side=tk.LEFT, padx=self.pad)
        self.table_dropdown.bind("<<ComboboxSelected>>", self.on_table_select)

        tk.Label(menu, text="Søk:", bg='#f0f8ff').pack(side=tk.LEFT, padx=(self.pad,0))
        self.search_entry = tk.Entry(menu, font=("Arial",self.base_font_size), width=self.entry_width)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=self.pad)
        self.search_entry.bind('<KeyRelease>', self.perform_search)

        tk.Label(menu, text="Sorter etter:", bg='#f0f8ff').pack(side=tk.LEFT, padx=(self.pad,0))
        self.sort_var = tk.StringVar()
        self.sort_combobox = ttk.Combobox(menu, textvariable=self.sort_var, state="readonly", width=self.combo_width)
        self.sort_combobox.pack(side=tk.LEFT, padx=self.pad)
        ttk.Button(menu, text="Sorter", command=self.sort_results).pack(side=tk.LEFT, padx=self.pad)

        # Paneler
        left = tk.Frame(self.root, bg='#f0f8ff')
        left.pack(side=tk.LEFT, fill=tk.Y, padx=self.pad, pady=self.pad)
        if self.user_role!='elev':
            self.data_entry_frame = ttk.Labelframe(left, text="Legg til/Endre")
            self.data_entry_frame.pack(fill=tk.X, pady=self.pad)
            self.build_data_entry()
        details = ttk.Labelframe(left, text="Detaljer")
        details.pack(fill=tk.BOTH, expand=True, pady=self.pad)
        self.details_text=tk.Text(details, state='disabled', wrap='word', font=("Arial",self.base_font_size))
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=self.pad, pady=self.pad)

        right = tk.Frame(self.root, bg='#f0f8ff')
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=self.pad, pady=self.pad)
        self.build_results(right)

        # Status
        self.status_var = tk.StringVar("Velg en tabell for å starte...")
        status = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor='w', font=("Arial",self.base_font_size), bg='white', fg='#2c3e50')
        status.pack(side=tk.BOTTOM, fill=tk.X)

    def build_data_entry(self):
        # ... implementasjon for data entry (samme logikk som før) ...
        pass

    def build_results(self, parent):
        self.results_tree = ttk.Treeview(parent, selectmode='browse')
        self.results_tree.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.results_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscroll=scrollbar.set)
        self.results_tree.bind("<<TreeviewSelect>>", self.on_result_select)

        action_frame = tk.Frame(parent, bg='#f0f8ff')
        action_frame.pack(fill=tk.X, pady=self.pad)
        if self.user_role!='elev':
            for txt,cmd in [("Legg til",self.add_record),("Rediger",self.populate_form_for_selected),("Oppdater post",self.update_selected_record),("Oppdater alle",self.update_all_records),("Slett valgte",self.delete_records),("Tøm skjema",self.clear_form)]:
                ttk.Button(action_frame, text=txt, command=cmd).pack(side=tk.LEFT, padx=5)

    def clear_form(self):
        if hasattr(self,'entry_widgets'):
            for w in self.entry_widgets.values(): w.delete(0,tk.END)
        self.details_text.configure(state='normal')
        self.details_text.delete('1.0',tk.END)
        self.details_text.configure(state='disabled')
        if hasattr(self,'selected_item'): del self.selected_item

    # ... øvrige metoder for CRUD, søk, sort, navigasjon beholdes uendret ...


def main():
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()
```

**Hvorfor ser man ikke "tabellene" i koden?**
Alle tabellene er definert i `self.tables`-ordboken i konstruktøren til `SchoolDatabaseApp`. Koden henter ikke fra en nettside, men bruker denne statiske strukturen for å generere dropdown, felter og SQL-spørringer dynamisk. Hvis du vil se alle tabellene, må du utvide `self.tables`-dictionary-en med tabellnavnene og spørringene slik jeg har vist for de første par tabellene.
