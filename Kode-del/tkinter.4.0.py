import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

#############################
# Database Manager Klasse   #
#############################
class DatabaseManager:
    def __init__(self, config):
        self.config = config

    def execute_query(self, query, params=(), commit=False):
        conn = None
        result = None
        try:
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor()
            cursor.execute(query, params)
            if commit:
                conn.commit()
            else:
                result = cursor.fetchall()
            return result
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
            return None
        finally:
            if conn:
                conn.close()

#############################
# Hoved GUI Applikasjon     #
#############################
class SchoolDatabaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("School Database Management")
        self.root.geometry("1400x800")
        self.root.configure(bg='#f0f4f8')
        
        # Oppdaterte DB-konfigurasjon
        self.DB_CONFIG = {
            'host': "10.10.25.50",
            'user': "dennis",
            'password': "dennis",
            'database': "Skoleapplikasjon"
        }
        self.db_manager = DatabaseManager(self.DB_CONFIG)
        
        # Tabelldefinisjoner med felt, spørringer og primærnøkler
        self.tables = {
            "rolle": {
                "fields": ["rolle_navn"],
                "primary_key": ["rolle_navn"],
                "insert_query": "INSERT INTO rolle (rolle_navn) VALUES (%s)",
                "select_query": "SELECT * FROM rolle"
            },
            "brukere": {
                "fields": ["fornavn", "etternavn", "rolle_navn"],
                "primary_key": ["fornavn", "etternavn"],
                "insert_query": "INSERT INTO brukere (fornavn, etternavn, rolle_navn) VALUES (%s, %s, %s)",
                "select_query": "SELECT * FROM brukere"
            },
            "admin": {
                "fields": ["fornavn", "etternavn"],
                "primary_key": ["fornavn", "etternavn"],
                "insert_query": "INSERT INTO admin (fornavn, etternavn) VALUES (%s, %s)",
                "select_query": "SELECT * FROM admin"
            },
            "laerer": {
                "fields": ["fornavn", "etternavn", "fag", "alder"],
                "primary_key": ["fornavn", "etternavn"],
                "insert_query": "INSERT INTO laerer (fornavn, etternavn, fag, alder) VALUES (%s, %s, %s, %s)",
                "select_query": "SELECT * FROM laerer"
            },
            "elever": {
                "fields": ["fornavn", "etternavn", "trinn", "fodselsdato"],
                "primary_key": ["fornavn", "etternavn"],
                "insert_query": "INSERT INTO elever (fornavn, etternavn, trinn, fodselsdato) VALUES (%s, %s, %s, %s)",
                "select_query": "SELECT * FROM elever"
            },
            "fag": {
                "fields": ["fag_navn"],
                "primary_key": ["fag_navn"],
                "insert_query": "INSERT INTO fag (fag_navn) VALUES (%s)",
                "select_query": "SELECT * FROM fag"
            },
            "elev_fag": {
                "fields": ["fornavn", "etternavn", "fag_navn", "karakter"],
                "primary_key": ["fornavn", "etternavn", "fag_navn"],
                "insert_query": "INSERT INTO elev_fag (fornavn, etternavn, fag_navn, karakter) VALUES (%s, %s, %s, %s)",
                "select_query": "SELECT * FROM elev_fag"
            },
            "oppgaver": {
                "fields": ["fornavn", "etternavn", "oppgave_tekst", "fag_navn"],
                "primary_key": ["fornavn", "etternavn", "oppgave_tekst"],
                "insert_query": "INSERT INTO oppgaver (fornavn, etternavn, oppgave_tekst, fag_navn) VALUES (%s, %s, %s, %s)",
                "select_query": "SELECT * FROM oppgaver"
            },
            "fravaer": {
                "fields": ["fornavn", "etternavn", "dato", "antall_timer"],
                "primary_key": ["fornavn", "etternavn", "dato"],
                "insert_query": "INSERT INTO fravaer (fornavn, etternavn, dato, antall_timer) VALUES (%s, %s, %s, %s)",
                "select_query": "SELECT * FROM fravaer"
            },
            "klasse": {
                "fields": ["klasse_navn"],
                "primary_key": ["klasse_navn"],
                "insert_query": "INSERT INTO klasse (klasse_navn) VALUES (%s)",
                "select_query": "SELECT * FROM klasse"
            },
            "klasse_elev": {
                "fields": ["klasse_navn", "fornavn", "etternavn"],
                "primary_key": ["klasse_navn", "fornavn", "etternavn"],
                "insert_query": "INSERT INTO klasse_elev (klasse_navn, fornavn, etternavn) VALUES (%s, %s, %s)",
                "select_query": "SELECT * FROM klasse_elev"
            },
            "klasse_laerer": {
                "fields": ["klasse_navn", "fornavn", "etternavn"],
                "primary_key": ["klasse_navn", "fornavn", "etternavn"],
                "insert_query": "INSERT INTO klasse_laerer (klasse_navn, fornavn, etternavn) VALUES (%s, %s, %s)",
                "select_query": "SELECT * FROM klasse_laerer"
            },
            "kontroll": {
                "fields": ["fornavn", "etternavn", "beskrivelse", "dato"],
                "primary_key": ["fornavn", "etternavn", "dato"],
                "insert_query": "INSERT INTO kontroll (fornavn, etternavn, beskrivelse, dato) VALUES (%s, %s, %s, %s)",
                "select_query": "SELECT * FROM kontroll"
            },
            "devices": {
                "fields": ["fornavn", "etternavn", "device_type", "device_model"],
                "primary_key": ["fornavn", "etternavn", "device_type", "device_model"],
                "insert_query": "INSERT INTO devices (fornavn, etternavn, device_type, device_model) VALUES (%s, %s, %s, %s)",
                "select_query": "SELECT * FROM devices"
            },
            "postdata": {
                "fields": ["fornavn", "etternavn", "innhold", "tidspunkt"],
                "primary_key": ["fornavn", "etternavn", "tidspunkt"],
                "insert_query": "INSERT INTO postdata (fornavn, etternavn, innhold, tidspunkt) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)",
                "select_query": "SELECT * FROM postdata"
            },
            "start": {
                "fields": ["innstilling", "verdi"],
                "primary_key": ["innstilling"],
                "insert_query": "INSERT INTO start (innstilling, verdi) VALUES (%s, %s)",
                "select_query": "SELECT * FROM start"
            }
        }  # Endelig tabell-definisjon

        self.create_main_layout()

    def create_main_layout(self):
        # Øverste ramme med menylinje
        self.main_frame = tk.Frame(self.root, bg='#f0f4f8')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Meny / verktøylinje
        self.menu_frame = tk.Frame(self.main_frame, bg='#f0f4f8')
        self.menu_frame.pack(fill=tk.X, pady=5)

        tk.Label(self.menu_frame, text="Tabell:", bg='#f0f4f8', font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(5,0))
        self.table_var = tk.StringVar()
        self.table_dropdown = ttk.Combobox(self.menu_frame, textvariable=self.table_var,
                                           values=list(self.tables.keys()), state="readonly", width=30)
        self.table_dropdown.pack(side=tk.LEFT, padx=5)
        self.table_dropdown.bind("<<ComboboxSelected>>", self.on_table_select)

        # Søkefunksjon
        search_frame = tk.Frame(self.menu_frame, bg='#f0f4f8')
        search_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        tk.Label(search_frame, text="Søk:", bg='#f0f4f8').pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, width=50)
        self.search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.search_entry.bind('<KeyRelease>', self.perform_search)

        # Hovedinnhold: Dataregistrering, resultatområde og detaljer
        self.content_frame = tk.Frame(self.main_frame, bg='#f0f4f8')
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.create_data_entry_frame()
        self.create_results_frame()
        self.create_details_frame()
        self.create_status_bar()

    def create_data_entry_frame(self):
        self.data_entry_frame = tk.LabelFrame(self.content_frame, text="Legg til/Endre", bg='#ffffff', font=("Arial", 10, "bold"))
        self.data_entry_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10), pady=5)
        self.entry_widgets = {}

    def create_results_frame(self):
        self.results_frame = tk.Frame(self.content_frame, bg='#f0f4f8')
        self.results_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)

        self.results_tree = ttk.Treeview(self.results_frame, selectmode='browse')
        self.results_tree.pack(fill=tk.BOTH, expand=True, anchor='w')
        self.results_tree.bind('<<TreeviewSelect>>', self.on_result_select)
        self.results_tree.bind('<Double-1>', self.on_result_double_click)

        scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscroll=scrollbar.set)

        # Handling for knapper under treview
        action_frame = tk.Frame(self.results_frame, bg='#f0f4f8')
        action_frame.pack(fill=tk.X, pady=5)
        ttk.Button(action_frame, text="Legg til", command=self.add_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Oppdater valgt", command=self.update_selected_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Oppdater alle", command=self.update_all_records).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Slett", command=self.delete_records).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Tøm skjema", command=self.clear_form).pack(side=tk.LEFT, padx=5)

    def create_details_frame(self):
        self.details_frame = tk.LabelFrame(self.content_frame, text="Detaljer", bg='#e8f0fe', font=("Arial", 10, "bold"))
        self.details_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10,0), pady=5)
        self.details_text = tk.Text(self.details_frame, height=30, state='disabled', wrap='word', bg='#ffffff')
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("Velg en tabell for å starte...")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor='w', font=("Arial", 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def clear_form(self):
        # Tømmer alle inndatafelt og detaljer
        for widget in self.entry_widgets.values():
            widget.delete(0, tk.END)
        self.details_text.configure(state='normal')
        self.details_text.delete('1.0', tk.END)
        self.details_text.configure(state='disabled')
        if hasattr(self, 'selected_item'):
            del self.selected_item

    def on_table_select(self, event=None):
        self.clear_form()
        selected_table = self.table_var.get()
        if not selected_table:
            return

        # Fjern gamle widgets i data_entry_frame
        for widget in self.data_entry_frame.winfo_children():
            widget.destroy()
        self.entry_widgets = {}

        # Lag inndatafelt for hvert felt definert for den valgte tabellen
        for field in self.tables[selected_table]['fields']:
            frame = tk.Frame(self.data_entry_frame, bg='#ffffff')
            frame.pack(fill=tk.X, padx=5, pady=3)
            label = tk.Label(frame, text=field + ":", width=15, anchor='w', bg='#ffffff', font=("Arial", 10))
            label.pack(side=tk.LEFT)
            entry = tk.Entry(frame, width=30, font=("Arial", 10))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.entry_widgets[field] = entry

        self.populate_results_tree(selected_table)
        self.status_var.set(f"Viser data for tabellen '{selected_table}'.")

    def populate_results_tree(self, table_name):
        # Tøm tidligere resultater
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Konfigurer kolonner: Liste med primærnøkkel+ øvrige felt
        columns = tuple(self.tables[table_name]['fields'])
        self.results_tree['columns'] = columns
        self.results_tree.heading("#0", text="")
        self.results_tree.column("#0", width=0, stretch=tk.NO)

        for field in columns:
            self.results_tree.heading(field, text=field)
            self.results_tree.column(field, anchor='center', width=120)

        rows = self.db_manager.execute_query(self.tables[table_name]['select_query'])
        if rows is None:
            return

        for row in rows:
            # Hvert rad settes inn i treet
            self.results_tree.insert('', 'end', values=row)
        self.status_var.set(f"{len(rows)} poster funnet i '{table_name}'.")

    def on_result_select(self, event):
        selected = self.results_tree.selection()
        if not selected:
            return
        # Plukk ut verdiene til den valgte raden
        values = self.results_tree.item(selected[0])['values']
        # Oppdater inndatafelt med verdiene
        for i, field in enumerate(self.tables[self.table_var.get()]['fields']):
            if i < len(values):
                self.entry_widgets[field].delete(0, tk.END)
                self.entry_widgets[field].insert(0, values[i])
        self.selected_item = selected[0]
        self.update_detail_box(self.entry_widgets)

    def on_result_double_click(self, event):
        # Ved dobbeltklikk vises detaljer for den valgte posten
        self.on_result_select(event)

    def update_detail_box(self, entry_widgets):
        self.details_text.configure(state='normal')
        self.details_text.delete('1.0', tk.END)
        for field, widget in entry_widgets.items():
            self.details_text.insert(tk.END, f"{field}: {widget.get()}\n")
        self.details_text.configure(state='disabled')

    def perform_search(self, event=None):
        search_term = self.search_entry.get().lower()
        selected_table = self.table_var.get()
        if not selected_table:
            return

        # Tømmer resultatene
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        query_result = self.db_manager.execute_query(self.tables[selected_table]['select_query'])
        if query_result is None:
            return

        match_count = 0
        for row in query_result:
            if any(search_term in str(val).lower() for val in row):
                self.results_tree.insert('', 'end', values=row)
                match_count += 1
        self.status_var.set(f"Søket fant {match_count} poster.")

    def add_record(self):
        selected_table = self.table_var.get()
        if not selected_table:
            messagebox.showwarning("Advarsel", "Velg en tabell først")
            return

        values = [widget.get().strip() for widget in self.entry_widgets.values()]
        if any(val == '' for val in values):
            messagebox.showwarning("Advarsel", "Alle felt må fylles ut")
            return

        query = self.tables[selected_table]['insert_query']
        if self.db_manager.execute_query(query, tuple(values), commit=True) is None:
            return

        messagebox.showinfo("Suksess", "Posten ble lagt til")
        self.clear_form()
        self.populate_results_tree(selected_table)

    def update_selected_record(self):
        selected_table = self.table_var.get()
        if not selected_table:
            messagebox.showwarning("Advarsel", "Velg en tabell først")
            return

        if not hasattr(self, 'selected_item'):
            messagebox.showwarning("Advarsel", "Velg en post å oppdatere")
            return

        fields = self.tables[selected_table]['fields']
        pk_fields = self.tables[selected_table]['primary_key']

        new_values = [self.entry_widgets[field].get().strip() for field in fields]
        if any(val == '' for val in new_values):
            messagebox.showwarning("Advarsel", "Alle felt må fylles ut")
            return

        # Hent originale verdier for primærnøkkelen fra den valgte posten
        current_values = self.results_tree.item(self.selected_item)['values']
        pk_indices = [fields.index(pk) for pk in pk_fields]

        where_clause = " AND ".join([f"{pk} = %s" for pk in pk_fields])
        update_query = f"UPDATE {selected_table} SET {', '.join([f'{field} = %s' for field in fields])} WHERE {where_clause}"
        # Kombiner de nye verdiene med verdiene for primærnøkkelen
        pk_values = [current_values[i] for i in pk_indices]
        full_values = new_values + pk_values

        if self.db_manager.execute_query(update_query, tuple(full_values), commit=True) is None:
            return

        messagebox.showinfo("Suksess", "Valgt post ble oppdatert")
        self.populate_results_tree(selected_table)

    def update_all_records(self):
        selected_table = self.table_var.get()
        if not selected_table:
            messagebox.showwarning("Advarsel", "Velg en tabell først")
            return

        fields = self.tables[selected_table]['fields']
        new_values = [self.entry_widgets[field].get().strip() for field in fields]
        if any(val == '' for val in new_values):
            messagebox.showwarning("Advarsel", "Alle felt må fylles ut")
            return

        if not messagebox.askyesno("Bekreft", "Er du sikker på at du vil oppdatere ALLE poster?"):
            return

        update_query = f"UPDATE {selected_table} SET {', '.join([f'{field} = %s' for field in fields])}"
        if self.db_manager.execute_query(update_query, tuple(new_values), commit=True) is None:
            return

        messagebox.showinfo("Suksess", f"Alle poster i '{selected_table}' ble oppdatert")
        self.populate_results_tree(selected_table)

    def delete_records(self):
        selected_table = self.table_var.get()
        if not selected_table:
            messagebox.showwarning("Advarsel", "Velg en tabell først")
            return

        # Bruker den valgte raden som skal slettes (bruker treeview sin markering)
        if not hasattr(self, 'selected_item'):
            messagebox.showwarning("Advarsel", "Velg en post å slette")
            return

        fields = self.tables[selected_table]['fields']
        pk_fields = self.tables[selected_table]['primary_key']
        current_values = self.results_tree.item(self.selected_item)['values']
        pk_indices = [fields.index(pk) for pk in pk_fields]
        pk_values = [current_values[i] for i in pk_indices]

        if not messagebox.askyesno("Bekreft", "Er du sikker på at du vil slette den valgte posten?"):
            return

        delete_query = f"DELETE FROM {selected_table} WHERE " + " AND ".join([f"{pk} = %s" for pk in pk_fields])
        if self.db_manager.execute_query(delete_query, tuple(pk_values), commit=True) is None:
            return

        messagebox.showinfo("Suksess", "Posten ble slettet")
        self.clear_form()
        self.populate_results_tree(selected_table)

def main():
    root = tk.Tk()
    app = SchoolDatabaseApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
