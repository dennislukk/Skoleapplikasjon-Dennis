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
        self.root.configure(bg='#ecf0f1')

        # Konfigurer ttk-stil
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "TButton",
            font=("Arial", 10, "bold"),
            background="#3498db",
            foreground="white",
            borderwidth=0
        )
        style.map("TButton", background=[("active", "#2980b9")])
        style.configure("TLabel", background="#ecf0f1", foreground="#2c3e50", font=("Arial", 10))
        style.configure("TEntry", font=("Arial", 10))
        style.configure("Treeview", background="white", foreground="#2c3e50",
                        font=("Arial", 10), fieldbackground="white")
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"),
                        background="#3498db", foreground="white")

        # Databasekonfig (tilpass til din DB)
        self.DB_CONFIG = {
            'host': "10.10.25.50",
            'user': "dennis",
            'password': "dennis",
            'database': "Skoleapplikasjon"
        }
        self.db_manager = DatabaseManager(self.DB_CONFIG)

        # Tabelldefinisjoner - juster som du vil
        self.tables = {
            "rolle": {
                "fields": ["rolle_navn"],
                "insert_query": "INSERT INTO rolle (rolle_navn) VALUES (%s)",
                "select_query": "SELECT * FROM rolle"
            },
            "brukere": {
                "fields": ["fornavn", "etternavn", "rolle_navn", "epost"],
                "insert_query": "INSERT INTO brukere (fornavn, etternavn, rolle_navn, epost) VALUES (%s, %s, %s, %s)",
                "select_query": "SELECT * FROM brukere",
                "foreign_keys": {
                    "rolle_navn": {
                        "table": "rolle",
                        "display_fields": ["rolle_navn"]
                    }
                }
            },
            "admin": {
                "fields": ["fornavn", "etternavn", "epost"],
                "insert_query": "INSERT INTO admin (fornavn, etternavn, epost) VALUES (%s, %s, %s)",
                "select_query": "SELECT * FROM admin",
                "foreign_keys": {
                    "fornavn": {"table": "brukere", "display_fields": ["fornavn"]},
                    "etternavn": {"table": "brukere", "display_fields": ["etternavn"]},
                    "epost": {"table": "brukere", "display_fields": ["epost"]}
                }
            },
            "laerer": {
                "fields": ["fornavn", "etternavn", "epost", "fag", "alder"],
                "insert_query": "INSERT INTO laerer (fornavn, etternavn, epost, fag, alder) VALUES (%s, %s, %s, %s, %s)",
                "select_query": "SELECT * FROM laerer",
                "foreign_keys": {
                    "fornavn": {"table": "brukere", "display_fields": ["fornavn"]},
                    "etternavn": {"table": "brukere", "display_fields": ["etternavn"]},
                    "epost": {"table": "brukere", "display_fields": ["epost"]},
                    "fag": {"table": "fag", "display_fields": ["fag_navn"]}
                }
            },
            "elever": {
                "fields": ["fornavn", "etternavn", "epost", "trinn", "fodselsdato"],
                "insert_query": "INSERT INTO elever (fornavn, etternavn, epost, trinn, fodselsdato) VALUES (%s, %s, %s, %s, %s)",
                "select_query": "SELECT * FROM elever",
                "foreign_keys": {
                    "fornavn": {"table": "brukere", "display_fields": ["fornavn"]},
                    "etternavn": {"table": "brukere", "display_fields": ["etternavn"]},
                    "epost": {"table": "brukere", "display_fields": ["epost"]}
                }
            },
            "fag": {
                "fields": ["fag_navn"],
                "insert_query": "INSERT INTO fag (fag_navn) VALUES (%s)",
                "select_query": "SELECT * FROM fag"
            },
            "elev_fag": {
                "fields": ["fornavn", "etternavn", "epost", "fag_navn", "karakter"],
                "insert_query": "INSERT INTO elev_fag (fornavn, etternavn, epost, fag_navn, karakter) VALUES (%s, %s, %s, %s, %s)",
                "select_query": "SELECT * FROM elev_fag",
                "foreign_keys": {
                    "fornavn": {"table": "brukere", "display_fields": ["fornavn"]},
                    "etternavn": {"table": "brukere", "display_fields": ["etternavn"]},
                    "epost": {"table": "brukere", "display_fields": ["epost"]},
                    "fag_navn": {"table": "fag", "display_fields": ["fag_navn"]}
                }
            },
            "oppgaver": {
                "fields": ["fornavn", "etternavn", "epost", "oppgave_tekst", "fag_navn"],
                "insert_query": "INSERT INTO oppgaver (fornavn, etternavn, epost, oppgave_tekst, fag_navn) VALUES (%s, %s, %s, %s, %s)",
                "select_query": "SELECT * FROM oppgaver",
                "foreign_keys": {
                    "fornavn": {"table": "brukere", "display_fields": ["fornavn"]},
                    "etternavn": {"table": "brukere", "display_fields": ["etternavn"]},
                    "epost": {"table": "brukere", "display_fields": ["epost"]},
                    "fag_navn": {"table": "fag", "display_fields": ["fag_navn"]}
                }
            },
            "fravaer": {
                "fields": ["fornavn", "etternavn", "epost", "dato", "antall_timer"],
                "insert_query": "INSERT INTO fravaer (fornavn, etternavn, epost, dato, antall_timer) VALUES (%s, %s, %s, %s, %s)",
                "select_query": "SELECT * FROM fravaer",
                "foreign_keys": {
                    "fornavn": {"table": "brukere", "display_fields": ["fornavn"]},
                    "etternavn": {"table": "brukere", "display_fields": ["etternavn"]},
                    "epost": {"table": "brukere", "display_fields": ["epost"]}
                }
            },
            "klasse": {
                "fields": ["klasse_navn"],
                "insert_query": "INSERT INTO klasse (klasse_navn) VALUES (%s)",
                "select_query": "SELECT * FROM klasse"
            },
            "klasse_elev": {
                "fields": ["klasse_navn", "fornavn", "etternavn", "epost"],
                "insert_query": "INSERT INTO klasse_elev (klasse_navn, fornavn, etternavn, epost) VALUES (%s, %s, %s, %s)",
                "select_query": "SELECT * FROM klasse_elev",
                "foreign_keys": {
                    "klasse_navn": {"table": "klasse", "display_fields": ["klasse_navn"]},
                    "fornavn": {"table": "brukere", "display_fields": ["fornavn"]},
                    "etternavn": {"table": "brukere", "display_fields": ["etternavn"]},
                    "epost": {"table": "brukere", "display_fields": ["epost"]}
                }
            },
            "klasse_laerer": {
                "fields": ["klasse_navn", "fornavn", "etternavn", "epost"],
                "insert_query": "INSERT INTO klasse_laerer (klasse_navn, fornavn, etternavn, epost) VALUES (%s, %s, %s, %s)",
                "select_query": "SELECT * FROM klasse_laerer",
                "foreign_keys": {
                    "klasse_navn": {"table": "klasse", "display_fields": ["klasse_navn"]},
                    "fornavn": {"table": "brukere", "display_fields": ["fornavn"]},
                    "etternavn": {"table": "brukere", "display_fields": ["etternavn"]},
                    "epost": {"table": "brukere", "display_fields": ["epost"]}
                }
            },
            "kontroll": {
                "fields": ["fornavn", "etternavn", "epost", "beskrivelse", "dato"],
                "insert_query": "INSERT INTO kontroll (fornavn, etternavn, epost, beskrivelse, dato) VALUES (%s, %s, %s, %s, %s)",
                "select_query": "SELECT * FROM kontroll",
                "foreign_keys": {
                    "fornavn": {"table": "brukere", "display_fields": ["fornavn"]},
                    "etternavn": {"table": "brukere", "display_fields": ["etternavn"]},
                    "epost": {"table": "brukere", "display_fields": ["epost"]}
                }
            },
            "devices": {
                "fields": ["fornavn", "etternavn", "epost", "device_type", "device_model"],
                "insert_query": "INSERT INTO devices (fornavn, etternavn, epost, device_type, device_model) VALUES (%s, %s, %s, %s, %s)",
                "select_query": "SELECT * FROM devices",
                "foreign_keys": {
                    "fornavn": {"table": "brukere", "display_fields": ["fornavn"]},
                    "etternavn": {"table": "brukere", "display_fields": ["etternavn"]},
                    "epost": {"table": "brukere", "display_fields": ["epost"]}
                }
            },
            "postdata": {
                "fields": ["fornavn", "etternavn", "epost", "innhold", "tidspunkt"],
                "insert_query": "INSERT INTO postdata (fornavn, etternavn, epost, innhold, tidspunkt) VALUES (%s, %s, %s, %s, %s)",
                "select_query": "SELECT * FROM postdata",
                "foreign_keys": {
                    "fornavn": {"table": "brukere", "display_fields": ["fornavn"]},
                    "etternavn": {"table": "brukere", "display_fields": ["etternavn"]},
                    "epost": {"table": "brukere", "display_fields": ["epost"]}
                }
            },
            "start": {
                "fields": ["innstilling", "verdi"],
                "insert_query": "INSERT INTO start (innstilling, verdi) VALUES (%s, %s)",
                "select_query": "SELECT * FROM start"
            }
        }

        self.create_main_layout()

    #############################################
    # Opprett GUI-strukturen
    #############################################
    def create_main_layout(self):
        self.main_frame = tk.Frame(self.root, bg='#ecf0f1')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Topplinje: Tabellvalg + Søk
        self.menu_frame = tk.Frame(self.main_frame, bg='#ecf0f1')
        self.menu_frame.pack(fill=tk.X, pady=5)

        tk.Label(self.menu_frame, text="Tabell:", bg='#ecf0f1',
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(5,0))

        self.table_var = tk.StringVar()
        self.table_dropdown = ttk.Combobox(
            self.menu_frame,
            textvariable=self.table_var,
            values=list(self.tables.keys()),
            state="readonly",
            width=30
        )
        self.table_dropdown.pack(side=tk.LEFT, padx=5)
        self.table_dropdown.bind("<<ComboboxSelected>>", self.on_table_select)

        # Søk
        search_frame = tk.Frame(self.menu_frame, bg='#ecf0f1')
        search_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Label(search_frame, text="Søk:", bg='#ecf0f1').pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, width=50)
        self.search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.search_entry.bind('<KeyRelease>', self.perform_search)

        # Innholdsområder
        self.content_frame = tk.Frame(self.main_frame, bg='#ecf0f1')
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.create_data_entry_frame()
        self.create_results_frame()
        self.create_details_frame()
        self.create_status_bar()

    def create_data_entry_frame(self):
        self.data_entry_frame = tk.LabelFrame(
            self.content_frame,
            text="Legg til/Endre",
            bg='white',
            font=("Arial", 10, "bold")
        )
        self.data_entry_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10), pady=5)
        self.entry_widgets = {}

    def create_results_frame(self):
        self.results_frame = tk.Frame(self.content_frame, bg='#ecf0f1')
        self.results_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)

        # Mulighet for å markere flere rader
        self.results_tree = ttk.Treeview(self.results_frame, selectmode='extended')
        self.results_tree.pack(fill=tk.BOTH, expand=True, anchor='w')

        scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL,
                                  command=self.results_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscroll=scrollbar.set)

        # Oppdater detaljeboks automatisk
        self.results_tree.bind("<<TreeviewSelect>>", self.on_result_select)

        # Handlingsknapper
        action_frame = tk.Frame(self.results_frame, bg='#ecf0f1')
        action_frame.pack(fill=tk.X, pady=5)

        ttk.Button(action_frame, text="Legg til", command=self.add_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Rediger", command=self.populate_form_for_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Oppdater post", command=self.update_selected_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Oppdater alle", command=self.update_all_records).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Slett valgte", command=self.delete_records).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Tøm skjema", command=self.clear_form).pack(side=tk.LEFT, padx=5)

    def create_details_frame(self):
        self.details_frame = tk.LabelFrame(
            self.content_frame,
            text="Detaljer",
            bg='#f7f9fa',
            font=("Arial", 10, "bold")
        )
        self.details_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10,0), pady=5)
        self.details_text = tk.Text(self.details_frame, height=30,
                                    state='disabled', wrap='word', bg='white')
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("Velg en tabell for å starte...")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1,
                                   relief=tk.SUNKEN, anchor='w',
                                   font=("Arial", 9), bg='white', fg='#2c3e50')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    #############################################
    # Støttefunksjoner
    #############################################
    def reselect_first_row(self):
        """
        Marker første rad (om den finnes) og oppdater detaljeboksen.
        Kalles hver gang resultattabellen er oppdatert.
        """
        children = self.results_tree.get_children()
        if children:
            self.results_tree.selection_set(children[0])
        else:
            self.details_text.configure(state='normal')
            self.details_text.delete('1.0', tk.END)
            self.details_text.insert(tk.END, "Ingen rad er valgt.")
            self.details_text.configure(state='disabled')

        # Kall on_result_select() for å oppdatere detaljeboks
        self.on_result_select()

    #############################################
    # Funksjoner
    #############################################
    def clear_form(self):
        for widget in self.entry_widgets.values():
            widget.delete(0, tk.END)
        self.details_text.configure(state='normal')
        self.details_text.delete('1.0', tk.END)
        self.details_text.configure(state='disabled')
        if hasattr(self, 'selected_item'):
            del self.selected_item

    def on_table_select(self, event=None):
        """
        Bygger inndatafelt for valgt tabell og oppdaterer resultater.
        """
        self.clear_form()
        selected_table = self.table_var.get()
        if not selected_table:
            return

        # Rens data_entry_frame
        for widget in self.data_entry_frame.winfo_children():
            widget.destroy()
        self.entry_widgets = {}

        # Lag inndatafelter
        table_info = self.tables[selected_table]
        foreign_keys = table_info.get("foreign_keys", {})

        for field in table_info['fields']:
            frame = tk.Frame(self.data_entry_frame, bg='white')
            frame.pack(fill=tk.X, padx=5, pady=3)
            label = tk.Label(frame, text=f"{field}:", width=15, anchor='w',
                             bg='white', font=("Arial", 10))
            label.pack(side=tk.LEFT)

            if field in foreign_keys:
                ref_table_name = foreign_keys[field]["table"]
                display_fields = foreign_keys[field]["display_fields"]
                ref_table_info = self.tables.get(ref_table_name)
                combobox_values = []
                if ref_table_info:
                    ref_data = self.db_manager.execute_query(ref_table_info['select_query'])
                    if ref_data:
                        idxs = [ref_table_info['fields'].index(d) for d in display_fields]
                        seen = set()
                        for row in ref_data:
                            display_texts = [str(row[i]) for i in idxs]
                            text = " ".join(display_texts)
                            if text not in seen:
                                seen.add(text)
                                combobox_values.append(text)
                entry = ttk.Combobox(frame, values=combobox_values,
                                     state="readonly", font=("Arial", 10))
            else:
                entry = tk.Entry(frame, width=30, font=("Arial", 10))

            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.entry_widgets[field] = entry

        self.populate_results_tree(selected_table)
        self.status_var.set(f"Viser data for tabellen '{selected_table}'.")

    def populate_results_tree(self, table_name):
        """
        Henter data fra tabellen og viser dem i Treeview.
        Markerer deretter første rad automatisk.
        """
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
        self.reselect_first_row()  # Marker første rad og oppdater detaljer

    def on_result_select(self, event=None):
        """
        Oppdaterer detaljeboksen basert på den første valgte raden.
        Hvis ingen rad er valgt, gi en melding.
        """
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
        """
        Søk i tabellen: Viser kun rader som matcher søketeksten i minst én kolonne.
        """
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
        # Etter søk: Marker første rad, om den finnes
        self.reselect_first_row()

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
        # **Oppdater umiddelbart**:
        self.populate_results_tree(selected_table)

    def populate_form_for_selected(self):
        """
        Tar den første markerte raden og fyller inndatafeltene.
        Selve DB-oppdateringen gjøres av Oppdater post.
        """
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
        """
        Viser i detaljeboksen hva som står i inndatafeltene akkurat nå.
        """
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
            f"UPDATE {selected_table} "
            f"SET {', '.join([f'{field} = %s' for field in fields])} "
            f"WHERE {where_clause}"
        )
        full_values = new_values + pk_values

        if self.db_manager.execute_query(update_query, tuple(full_values), commit=True) is None:
            return

        messagebox.showinfo("Suksess", "Valgt post ble oppdatert.")
        # Oppdater tabellen
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

        update_query = (
            f"UPDATE {selected_table} "
            f"SET {', '.join([f'{field} = %s' for field in fields])}"
        )
        if self.db_manager.execute_query(update_query, tuple(new_values), commit=True) is None:
            return

        messagebox.showinfo("Suksess", f"Alle poster i '{selected_table}' ble oppdatert.")
        self.populate_results_tree(selected_table)

    def delete_records(self):
        """
        Sletter alle markerte rader fra databasen.
        """
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
        self.clear_form()
        self.populate_results_tree(selected_table)

#############################################
# main
#############################################
def main():
    root = tk.Tk()
    app = SchoolDatabaseApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
