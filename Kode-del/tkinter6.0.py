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

##########################################
# Hoved GUI Applikasjon
##########################################
class SchoolDatabaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Skole Database Administrasjon")
        self.root.geometry("1400x800")
        self.root.configure(bg='#f0f8ff')  # Lys blå bakgrunn

        # Konfigurer ttk-stil (bruker en mer fargerik palett)
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
        
        # Databasekonfigurasjon (tilpass din egen)
        self.DB_CONFIG = {
            'host': "10.10.25.50",
            'user': "dennis",
            'password': "dennis",
            'database': "Skoleapplikasjon"
        }
        self.db_manager = DatabaseManager(self.DB_CONFIG)

        ##########################################
        # Oppdatert tabellstruktur med felt og fremmednøkler
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
                "fields": ["fornavn", "etternavn", "rolle_navn", "epost"],
                "insert_query": "INSERT INTO brukere (fornavn, etternavn, rolle_navn, epost) VALUES (%s, %s, %s, %s)",
                "select_query": "SELECT * FROM brukere",
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

    ##########################################
    # GUI-struktur
    ##########################################
    def create_main_layout(self):
        self.main_frame = tk.Frame(self.root, bg='#f0f8ff')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header med fargerik bakgrunn
        header_frame = tk.Frame(self.main_frame, bg='#2980b9')
        header_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        header_label = tk.Label(header_frame, text="Skole Database Administrasjon", bg='#2980b9',
                                fg='white', font=("Arial", 20, "bold"))
        header_label.pack(side=tk.LEFT, padx=10)

        # Ramme for tabellvalg, søk og sortering
        menu_frame = tk.Frame(self.main_frame, bg='#f0f8ff')
        menu_frame.pack(side=tk.TOP, fill=tk.X)
        tk.Label(menu_frame, text="Tabell:", bg='#f0f8ff', font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(5,0))
        self.table_var = tk.StringVar()
        self.table_dropdown = ttk.Combobox(menu_frame, textvariable=self.table_var,
                                           values=list(self.tables.keys()),
                                           state="readonly", width=30)
        self.table_dropdown.pack(side=tk.LEFT, padx=5)
        self.table_dropdown.bind("<<ComboboxSelected>>", self.on_table_select)

        # Søke-feltet
        search_frame = tk.Frame(menu_frame, bg='#f0f8ff')
        search_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Label(search_frame, text="Søk:", bg='#f0f8ff').pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, width=50)
        self.search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.search_entry.bind('<KeyRelease>', self.perform_search)

        # Sorteringsdel
        sort_frame = tk.Frame(menu_frame, bg='#f0f8ff')
        sort_frame.pack(side=tk.LEFT, padx=5)
        tk.Label(sort_frame, text="Sorter etter:", bg='#f0f8ff').pack(side=tk.LEFT)
        self.sort_var = tk.StringVar()
        self.sort_combobox = ttk.Combobox(sort_frame, textvariable=self.sort_var, state="readonly", width=20)
        self.sort_combobox.pack(side=tk.LEFT, padx=5)
        ttk.Button(sort_frame, text="Sorter", command=self.sort_results).pack(side=tk.LEFT)

        # Hovedinnhold: inndatafelt, resultattabell, detaljer
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
        ttk.Button(action_frame, text="Legg til", command=self.add_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Rediger", command=self.populate_form_for_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Oppdater post", command=self.update_selected_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Oppdater alle", command=self.update_all_records).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Slett valgte", command=self.delete_records).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Tøm skjema", command=self.clear_form).pack(side=tk.LEFT, padx=5)

    def create_details_frame(self):
        self.details_frame = ttk.LabelFrame(self.content_frame, text="Detaljer")
        self.details_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10,0), pady=5)
        self.details_text = tk.Text(self.details_frame, height=30, state='disabled', wrap='word', bg='white')
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("Velg en tabell for å starte...")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1,
                                   relief=tk.SUNKEN, anchor='w', font=("Arial", 9),
                                   bg='white', fg='#2c3e50')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    ##########################################
    # Støttefunksjoner og navigasjon
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

        # Bygg inndatafelt på nytt
        for widget in self.data_entry_frame.winfo_children():
            widget.destroy()
        self.entry_widgets = {}

        table_info = self.tables[selected_table]
        foreign_keys = table_info.get("foreign_keys", {})
        for field in table_info['fields']:
            frame = tk.Frame(self.data_entry_frame, bg='#dfe6e9')
            frame.pack(fill=tk.X, padx=5, pady=3)
            label = tk.Label(frame, text=f"{field}:", width=15, anchor='w', bg='#dfe6e9', font=("Arial", 10))
            label.pack(side=tk.LEFT)
            if field in foreign_keys:
                ref_table_name = foreign_keys[field]["table"]
                display_fields = foreign_keys[field]["display_fields"]
                ref_table_info = self.tables.get(ref_table_name)
                combobox_values = []
                if ref_table_info:
                    ref_data = self.db_manager.execute_query(ref_table_info['select_query'])
                    if ref_data:
                        idxs = [ref_table_info['fields'].index(d) for d in display_fields if d in ref_table_info['fields']]
                        seen = set()
                        for row in ref_data:
                            display_texts = [str(row[i]) for i in idxs]
                            text = " ".join(display_texts)
                            if text not in seen:
                                seen.add(text)
                                combobox_values.append(text)
                entry = ttk.Combobox(frame, values=combobox_values, state="readonly", font=("Arial", 10))
            else:
                entry = tk.Entry(frame, width=30, font=("Arial", 10))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.entry_widgets[field] = entry

        # Sett sorteringsalternativer basert på tabellens felter
        sort_options = self.tables[selected_table]['fields']
        self.sort_combobox['values'] = sort_options
        self.sort_var.set(sort_options[0])
        
        self.populate_results_tree(selected_table)
        self.status_var.set(f"Viser data for tabellen '{selected_table}'.")

    def populate_results_tree(self, table_name):
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
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
            self.results_tree.insert('', 'end', values=row)
        self.status_var.set(f"{len(rows)} poster funnet i '{table_name}'.")
        self.reselect_first_row()

    def on_result_select(self, event=None):
        selected_items = self.results_tree.selection()
        if not selected_items:
            self.details_text.configure(state='normal')
            self.details_text.delete('1.0', tk.END)
            self.details_text.insert(tk.END, "Ingen rad er valgt.")
            self.details_text.configure(state='disabled')
            return
        first_item = selected_items[0]
        selected_table = self.table_var.get()
        fields = self.tables[selected_table]['fields']
        values = self.results_tree.item(first_item)['values']
        self.details_text.configure(state='normal')
        self.details_text.delete('1.0', tk.END)
        for field, val in zip(fields, values):
            self.details_text.insert(tk.END, f"{field}: {val}\n")
        self.details_text.configure(state='disabled')

    def perform_search(self, event=None):
        selected_table = self.table_var.get()
        if not selected_table:
            return
        search_term = self.search_entry.get().lower().strip()
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
        self.reselect_first_row()

    ##########################################
    # CRUD-funksjoner
    ##########################################
    def add_record(self):
        selected_table = self.table_var.get()
        if not selected_table:
            messagebox.showwarning("Advarsel", "Velg en tabell først.")
            return
        values = [widget.get().strip() for widget in self.entry_widgets.values()]
        if any(val == '' for val in values):
            messagebox.showwarning("Advarsel", "Alle felt må fylles ut (eller sett default i DB).")
            return
        query = self.tables[selected_table]['insert_query']
        if self.db_manager.execute_query(query, tuple(values), commit=True) is None:
            return
        messagebox.showinfo("Suksess", "Posten ble lagt til.")
        self.clear_form()
        # Vent litt før vi henter oppdatert data slik at databasen rekker å oppdatere
        self.root.after(100, lambda: self.populate_results_tree(selected_table))

    def populate_form_for_selected(self):
        selected_items = self.results_tree.selection()
        if not selected_items:
            messagebox.showwarning("Advarsel", "Velg en rad i tabellen først.")
            return
        self.selected_item = selected_items[0]
        selected_table = self.table_var.get()
        fields = self.tables[selected_table]['fields']
        values = self.results_tree.item(self.selected_item)['values']
        for i, field in enumerate(fields):
            widget = self.entry_widgets[field]
            widget.delete(0, tk.END)
            widget.insert(0, str(values[i]) if i < len(values) else "")
        self.update_detail_box()

    def update_detail_box(self):
        self.details_text.configure(state='normal')
        self.details_text.delete('1.0', tk.END)
        for field, widget in self.entry_widgets.items():
            self.details_text.insert(tk.END, f"{field}: {widget.get()}\n")
        self.details_text.configure(state='disabled')

    def update_selected_record(self):
        selected_table = self.table_var.get()
        if not selected_table:
            messagebox.showwarning("Advarsel", "Velg en tabell først.")
            return
        if not hasattr(self, 'selected_item'):
            messagebox.showwarning("Advarsel", "Du må først trykke 'Rediger' for å hente data til skjemaet.")
            return
        fields = self.tables[selected_table]['fields']
        pk_fields = self.tables[selected_table].get('primary_key', fields)
        new_values = [self.entry_widgets[field].get().strip() for field in fields]
        if any(val == '' for val in new_values):
            messagebox.showwarning("Advarsel", "Alle felt må fylles ut.")
            return
        current_values = self.results_tree.item(self.selected_item)['values']
        pk_indices = [fields.index(pk) for pk in pk_fields]
        pk_values = [current_values[i] for i in pk_indices]
        where_clause = " AND ".join([f"{pk} = %s" for pk in pk_fields])
        update_query = (
            f"UPDATE {selected_table} SET {', '.join([f'{field} = %s' for field in fields])} "
            f"WHERE {where_clause}"
        )
        full_values = new_values + pk_values
        if self.db_manager.execute_query(update_query, tuple(full_values), commit=True) is None:
            return
        messagebox.showinfo("Suksess", "Valgt post ble oppdatert.")
        self.populate_results_tree(selected_table)

    def update_all_records(self):
        selected_table = self.table_var.get()
        if not selected_table:
            messagebox.showwarning("Advarsel", "Velg en tabell først.")
            return
        fields = self.tables[selected_table]['fields']
        new_values = [self.entry_widgets[field].get().strip() for field in fields]
        if any(val == '' for val in new_values):
            messagebox.showwarning("Advarsel", "Alle felt må fylles ut.")
            return
        if not messagebox.askyesno("Bekreft", "Er du sikker på at du vil oppdatere ALLE poster?"):
            return
        update_query = f"UPDATE {selected_table} SET {', '.join([f'{field} = %s' for field in fields])}"
        if self.db_manager.execute_query(update_query, tuple(new_values), commit=True) is None:
            return
        messagebox.showinfo("Suksess", f"Alle poster i '{selected_table}' ble oppdatert.")
        self.populate_results_tree(selected_table)

    def delete_records(self):
        selected_table = self.table_var.get()
        if not selected_table:
            messagebox.showwarning("Advarsel", "Velg en tabell først.")
            return
        selected_items = self.results_tree.selection()
        if not selected_items:
            messagebox.showwarning("Advarsel", "Velg en eller flere rader i tabellen først.")
            return
        if not messagebox.askyesno("Bekreft", f"Vil du slette de {len(selected_items)} valgte postene?"):
            return
        fields = self.tables[selected_table]['fields']
        pk_fields = self.tables[selected_table].get('primary_key', fields)
        delete_query = f"DELETE FROM {selected_table} WHERE " + " AND ".join([f"{pk} = %s" for pk in pk_fields])
        deleted_count = 0
        for item in selected_items:
            row_values = self.results_tree.item(item)['values']
            pk_indices = [fields.index(pk) for pk in pk_fields]
            pk_values = [row_values[i] for i in pk_indices]
            if self.db_manager.execute_query(delete_query, tuple(pk_values), commit=True) is None:
                return
            deleted_count += 1
        messagebox.showinfo("Suksess", f"{deleted_count} poster ble slettet.")
        self.populate_results_tree(selected_table)

    ##########################################
    # Sorteringsfunksjonalitet
    ##########################################
    def sort_results(self):
        selected_table = self.table_var.get()
        if not selected_table:
            messagebox.showwarning("Advarsel", "Velg en tabell først.")
            return
        sort_col = self.sort_var.get()
        if not sort_col:
            messagebox.showinfo("Sorter", "Velg en kolonne å sortere etter.")
            return
        # Bygg spørring med ORDER BY
        sort_query = self.tables[selected_table]['select_query'] + f" ORDER BY {sort_col} ASC"
        rows = self.db_manager.execute_query(sort_query)
        if rows is None:
            return
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        for row in rows:
            self.results_tree.insert('', 'end', values=row)
        self.status_var.set(f"{len(rows)} poster funnet i '{selected_table}' sortert etter {sort_col}.")
        self.reselect_first_row()

##########################################
# Main
##########################################
def main():
    root = tk.Tk()
    app = SchoolDatabaseApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
