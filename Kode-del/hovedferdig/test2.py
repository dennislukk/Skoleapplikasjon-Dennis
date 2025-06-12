import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector
from datetime import datetime, date
import re

class HaarOgBlomsterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HaarOgBlomster - Administrasjonssystem")
        self.root.geometry("1400x800")
        self.root.configure(bg='#f0f0f0')
        
        # Database konfigurasjon
        self.db_config = {
            'host': "10.10.25.55",
            'user': "dennis",
            'password': "r6dexMHMNE",
            'database': "HaarOgBlomster"
        }
        
        # Fargepalett
        self.colors = {
            'primary': '#2E8B57',      # SeaGreen
            'secondary': '#98FB98',     # PaleGreen
            'accent': '#FFB6C1',       # LightPink
            'bg': '#f8f9fa',           # Light gray
            'card_bg': '#ffffff',      # White
            'text': '#2c3e50',         # Dark blue-gray
            'success': '#28a745',      # Green
            'warning': '#ffc107',      # Yellow
            'danger': '#dc3545'        # Red
        }
        
        self.setup_styles()
        self.create_main_interface()
        
    def setup_styles(self):
        """Setter opp moderne styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Konfigurer hovedstiler
        style.configure('Title.TLabel', 
                       font=('Helvetica', 24, 'bold'),
                       foreground=self.colors['primary'],
                       background=self.colors['bg'])
        
        style.configure('Heading.TLabel',
                       font=('Helvetica', 14, 'bold'),
                       foreground=self.colors['text'],
                       background=self.colors['card_bg'])
        
        style.configure('Card.TFrame',
                       background=self.colors['card_bg'],
                       relief='raised',
                       borderwidth=1)
        
        style.configure('Primary.TButton',
                       font=('Helvetica', 10, 'bold'),
                       foreground='white')
        
        style.map('Primary.TButton',
                 background=[('active', self.colors['primary']),
                           ('!active', self.colors['primary'])])
        
    def create_main_interface(self):
        """Oppretter hovedgrensesnittet"""
        # Hovedcontainer
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Tittel
        title_label = ttk.Label(main_frame, text="🌸 HaarOgBlomster 💇‍♀️", style='Title.TLabel')
        title_label.pack(pady=(0, 30))
        
        # Notebook for faner
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Opprett faner
        self.create_dashboard_tab()
        self.create_customers_tab()
        self.create_appointments_tab()
        self.create_inventory_tab()
        self.create_employees_tab()
        
    def create_dashboard_tab(self):
        """Opprett dashbord-fane"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="📊 Dashbord")
        
        # Dashboard innhold
        welcome_frame = ttk.Frame(dashboard_frame, style='Card.TFrame')
        welcome_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Label(welcome_frame, text="Velkommen til HaarOgBlomster!", 
                 style='Heading.TLabel').pack(pady=20)
        
        # Statistikk-kort
        stats_frame = tk.Frame(dashboard_frame, bg=self.colors['bg'])
        stats_frame.pack(fill='x', padx=20, pady=10)
        
        self.create_stat_card(stats_frame, "Totalt Kunder", self.get_customer_count, 0, 0)
        self.create_stat_card(stats_frame, "Avtaler i dag", self.get_todays_appointments, 0, 1)
        self.create_stat_card(stats_frame, "Produkter på lager", self.get_inventory_count, 0, 2)
        self.create_stat_card(stats_frame, "Ansatte", self.get_employee_count, 0, 3)
        
        # Hurtigtilgang
        quick_frame = ttk.LabelFrame(dashboard_frame, text="Hurtigtilgang", padding=20)
        quick_frame.pack(fill='x', padx=20, pady=20)
        
        button_frame = tk.Frame(quick_frame, bg=self.colors['card_bg'])
        button_frame.pack()
        
        ttk.Button(button_frame, text="➕ Ny Kunde", 
                  command=self.new_customer_dialog, style='Primary.TButton').grid(row=0, column=0, padx=10, pady=5)
        ttk.Button(button_frame, text="📅 Ny Avtale", 
                  command=self.new_appointment_dialog, style='Primary.TButton').grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(button_frame, text="📦 Legg til Produkt", 
                  command=self.new_product_dialog, style='Primary.TButton').grid(row=0, column=2, padx=10, pady=5)
        
    def create_stat_card(self, parent, title, value_func, row, col):
        """Opprett statistikk-kort"""
        card = tk.Frame(parent, bg=self.colors['card_bg'], relief='raised', bd=2)
        card.grid(row=row, column=col, padx=10, pady=10, sticky='ew')
        parent.grid_columnconfigure(col, weight=1)
        
        ttk.Label(card, text=title, font=('Helvetica', 10)).pack(pady=(10, 5))
        value_label = ttk.Label(card, text=str(value_func()), font=('Helvetica', 20, 'bold'))
        value_label.pack(pady=(0, 10))
        
    def create_customers_tab(self):
        """Opprett kunde-fane"""
        customers_frame = ttk.Frame(self.notebook)
        self.notebook.add(customers_frame, text="👥 Kunder")
        
        # Toolbar
        toolbar = tk.Frame(customers_frame, bg=self.colors['bg'], height=60)
        toolbar.pack(fill='x', padx=20, pady=(20, 10))
        toolbar.pack_propagate(False)
        
        ttk.Button(toolbar, text="➕ Ny Kunde", command=self.new_customer_dialog).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="✏️ Rediger", command=self.edit_customer).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="🗑️ Slett", command=self.delete_customer).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="🔄 Oppdater", command=self.refresh_customers).pack(side='left', padx=(0, 10))
        
        # Søkefelt
        search_frame = tk.Frame(toolbar, bg=self.colors['bg'])
        search_frame.pack(side='right')
        ttk.Label(search_frame, text="Søk:", background=self.colors['bg']).pack(side='left', padx=(0, 5))
        self.customer_search_var = tk.StringVar()
        self.customer_search_var.trace('w', self.search_customers)
        ttk.Entry(search_frame, textvariable=self.customer_search_var, width=20).pack(side='left')
        
        # Tabell
        self.customers_tree = self.create_treeview(customers_frame, 
            ['ID', 'Fornavn', 'Etternavn', 'Telefon', 'E-post', 'Adresse', 'Opprettet'],
            [50, 100, 100, 100, 150, 200, 120])
        
        self.refresh_customers()
        
    def create_appointments_tab(self):
        """Opprett avtale-fane"""
        appointments_frame = ttk.Frame(self.notebook)
        self.notebook.add(appointments_frame, text="📅 Avtaler")
        
        # Toolbar
        toolbar = tk.Frame(appointments_frame, bg=self.colors['bg'], height=60)
        toolbar.pack(fill='x', padx=20, pady=(20, 10))
        toolbar.pack_propagate(False)
        
        ttk.Button(toolbar, text="➕ Ny Avtale", command=self.new_appointment_dialog).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="✏️ Rediger", command=self.edit_appointment).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="✅ Marker Fullført", command=self.complete_appointment).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="❌ Avlys", command=self.cancel_appointment).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="🔄 Oppdater", command=self.refresh_appointments).pack(side='left', padx=(0, 10))
        
        # Filter
        filter_frame = tk.Frame(toolbar, bg=self.colors['bg'])
        filter_frame.pack(side='right')
        ttk.Label(filter_frame, text="Status:", background=self.colors['bg']).pack(side='left', padx=(0, 5))
        self.appointment_filter = ttk.Combobox(filter_frame, values=['Alle', 'Planlagt', 'Fullført', 'Avlyst'], 
                                             state='readonly', width=10)
        self.appointment_filter.set('Alle')
        self.appointment_filter.bind('<<ComboboxSelected>>', self.filter_appointments)
        self.appointment_filter.pack(side='left')
        
        # Tabell
        self.appointments_tree = self.create_treeview(appointments_frame,
            ['ID', 'Kunde', 'Dato', 'Tidspunkt', 'Tjeneste', 'Status', 'Kommentar'],
            [50, 150, 100, 80, 150, 80, 200])
        
        self.refresh_appointments()
        
    def create_inventory_tab(self):
        """Opprett lager-fane"""
        inventory_frame = ttk.Frame(self.notebook)
        self.notebook.add(inventory_frame, text="📦 Lager")
        
        # Toolbar
        toolbar = tk.Frame(inventory_frame, bg=self.colors['bg'], height=60)
        toolbar.pack(fill='x', padx=20, pady=(20, 10))
        toolbar.pack_propagate(False)
        
        ttk.Button(toolbar, text="➕ Nytt Produkt", command=self.new_product_dialog).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="✏️ Rediger", command=self.edit_product).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="📈 Juster Antall", command=self.adjust_inventory).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="🗑️ Slett", command=self.delete_product).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="🔄 Oppdater", command=self.refresh_inventory).pack(side='left', padx=(0, 10))
        
        # Kategori-filter
        filter_frame = tk.Frame(toolbar, bg=self.colors['bg'])
        filter_frame.pack(side='right')
        ttk.Label(filter_frame, text="Kategori:", background=self.colors['bg']).pack(side='left', padx=(0, 5))
        self.inventory_filter = ttk.Combobox(filter_frame, values=['Alle'], state='readonly', width=15)
        self.inventory_filter.set('Alle')
        self.inventory_filter.bind('<<ComboboxSelected>>', self.filter_inventory)
        self.inventory_filter.pack(side='left')
        
        # Tabell
        self.inventory_tree = self.create_treeview(inventory_frame,
            ['ID', 'Navn', 'Kategori', 'Antall', 'Pris', 'Sist Oppdatert'],
            [50, 200, 120, 80, 100, 150])
        
        self.refresh_inventory()
        
    def create_employees_tab(self):
        """Opprett ansatt-fane"""
        employees_frame = ttk.Frame(self.notebook)
        self.notebook.add(employees_frame, text="👨‍💼 Ansatte")
        
        # Toolbar
        toolbar = tk.Frame(employees_frame, bg=self.colors['bg'], height=60)
        toolbar.pack(fill='x', padx=20, pady=(20, 10))
        toolbar.pack_propagate(False)
        
        ttk.Button(toolbar, text="➕ Ny Ansatt", command=self.new_employee_dialog).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="✏️ Rediger", command=self.edit_employee).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="🗑️ Slett", command=self.delete_employee).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="🔄 Oppdater", command=self.refresh_employees).pack(side='left', padx=(0, 10))
        
        # Tabell
        self.employees_tree = self.create_treeview(employees_frame,
            ['ID', 'Navn', 'Stilling', 'Telefon', 'E-post'],
            [50, 200, 150, 120, 200])
        
        self.refresh_employees()
        
    def create_treeview(self, parent, columns, widths):
        """Opprett en treeview med scrollbars"""
        # Frame for treeview og scrollbars
        tree_frame = tk.Frame(parent, bg=self.colors['bg'])
        tree_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Treeview
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Konfigurer kolonner
        for i, (col, width) in enumerate(zip(columns, widths)):
            tree.heading(col, text=col)
            tree.column(col, width=width, minwidth=50)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack alt
        tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        return tree
        
    def get_db_connection(self):
        """Få databaseforbindelse"""
        try:
            return mysql.connector.connect(**self.db_config)
        except mysql.connector.Error as err:
            messagebox.showerror("Database Feil", f"Kunne ikke koble til database: {err}")
            return None
            
    # Database funksjoner for statistikk
    def get_customer_count(self):
        conn = self.get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM Kunder")
                return cursor.fetchone()[0]
            except:
                return 0
            finally:
                conn.close()
        return 0
        
    def get_todays_appointments(self):
        conn = self.get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                today = date.today()
                cursor.execute("SELECT COUNT(*) FROM Avtaler WHERE dato = %s AND status = 'Planlagt'", (today,))
                return cursor.fetchone()[0]
            except:
                return 0
            finally:
                conn.close()
        return 0
        
    def get_inventory_count(self):
        conn = self.get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM Lager")
                return cursor.fetchone()[0]
            except:
                return 0
            finally:
                conn.close()
        return 0
        
    def get_employee_count(self):
        conn = self.get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM Ansatte")
                return cursor.fetchone()[0]
            except:
                return 0
            finally:
                conn.close()
        return 0
    
    def refresh_inventory(self):
        """Oppdater produktliste (lager)"""
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)

        conn = self.get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM Lager ORDER BY navn")
                for row in cursor.fetchall():
                    # Formater dato hvis den finnes
                    oppdatert = row[5].strftime("%d.%m.%Y %H:%M") if row[5] else ""
                    self.inventory_tree.insert('', 'end', values=(*row[:5], oppdatert))
            except mysql.connector.Error as err:
                messagebox.showerror("Feil", f"Kunne ikke hente produkter: {err}")
            finally:
                conn.close()

        
    # Kunde-funksjoner
    def refresh_customers(self):
        """Oppdater kundeliste"""
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
            
        conn = self.get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM Kunder ORDER BY etternavn, fornavn")
                for row in cursor.fetchall():
                    # Formater opprettelsesdato
                    formatted_date = row[6].strftime("%d.%m.%Y %H:%M") if row[6] else ""
                    self.customers_tree.insert('', 'end', values=(*row[:6], formatted_date))
            except mysql.connector.Error as err:
                messagebox.showerror("Feil", f"Kunne ikke hente kunder: {err}")
            finally:
                conn.close()
                
    def search_customers(self, *args):
        """Søk i kunder"""
        search_term = self.customer_search_var.get().lower()
        
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
            
        conn = self.get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                if search_term:
                    query = """SELECT * FROM Kunder 
                             WHERE LOWER(fornavn) LIKE %s 
                             OR LOWER(etternavn) LIKE %s 
                             OR LOWER(telefon) LIKE %s 
                             OR LOWER(epost) LIKE %s
                             ORDER BY etternavn, fornavn"""
                    cursor.execute(query, (f'%{search_term}%', f'%{search_term}%', 
                                         f'%{search_term}%', f'%{search_term}%'))
                else:
                    cursor.execute("SELECT * FROM Kunder ORDER BY etternavn, fornavn")
                    
                for row in cursor.fetchall():
                    formatted_date = row[6].strftime("%d.%m.%Y %H:%M") if row[6] else ""
                    self.customers_tree.insert('', 'end', values=(*row[:6], formatted_date))
            except mysql.connector.Error as err:
                messagebox.showerror("Feil", f"Søk feilet: {err}")
            finally:
                conn.close()
                
    def new_customer_dialog(self):
        """Dialog for ny kunde"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Ny Kunde")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors['bg'])
        
        # Senter vinduet
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Form
        frame = ttk.LabelFrame(dialog, text="Kundeinformasjon", padding=20)
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        fields = {}
        
        ttk.Label(frame, text="Fornavn:").grid(row=0, column=0, sticky='w', pady=5)
        fields['fornavn'] = ttk.Entry(frame, width=25)
        fields['fornavn'].grid(row=0, column=1, pady=5, padx=(10, 0))
        
        ttk.Label(frame, text="Etternavn:").grid(row=1, column=0, sticky='w', pady=5)
        fields['etternavn'] = ttk.Entry(frame, width=25)
        fields['etternavn'].grid(row=1, column=1, pady=5, padx=(10, 0))
        
        ttk.Label(frame, text="Telefon:").grid(row=2, column=0, sticky='w', pady=5)
        fields['telefon'] = ttk.Entry(frame, width=25)
        fields['telefon'].grid(row=2, column=1, pady=5, padx=(10, 0))
        
        ttk.Label(frame, text="E-post:").grid(row=3, column=0, sticky='w', pady=5)
        fields['epost'] = ttk.Entry(frame, width=25)
        fields['epost'].grid(row=3, column=1, pady=5, padx=(10, 0))
        
        ttk.Label(frame, text="Adresse:").grid(row=4, column=0, sticky='w', pady=5)
        fields['adresse'] = ttk.Entry(frame, width=25)
        fields['adresse'].grid(row=4, column=1, pady=5, padx=(10, 0))
        
        # Knapper
        button_frame = tk.Frame(frame, bg=self.colors['card_bg'])
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        def save_customer():
            # Validering
            if not fields['fornavn'].get() or not fields['etternavn'].get():
                messagebox.showerror("Feil", "Fornavn og etternavn er påkrevd!")
                return
                
            conn = self.get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    query = """INSERT INTO Kunder (fornavn, etternavn, telefon, epost, adresse) 
                             VALUES (%s, %s, %s, %s, %s)"""
                    cursor.execute(query, (
                        fields['fornavn'].get(),
                        fields['etternavn'].get(),
                        fields['telefon'].get(),
                        fields['epost'].get(),
                        fields['adresse'].get()
                    ))
                    conn.commit()
                    messagebox.showinfo("Suksess", "Kunde lagt til!")
                    dialog.destroy()
                    self.refresh_customers()
                except mysql.connector.Error as err:
                    messagebox.showerror("Feil", f"Kunne ikke lagre kunde: {err}")
                finally:
                    conn.close()
        
        ttk.Button(button_frame, text="Lagre", command=save_customer, style='Primary.TButton').pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="Avbryt", command=dialog.destroy).pack(side='left')
        
    def edit_customer(self):
        """Rediger valgt kunde"""
        selection = self.customers_tree.selection()
        if not selection:
            messagebox.showwarning("Advarsel", "Vennligst velg en kunde å redigere.")
            return
            
        item = self.customers_tree.item(selection[0])
        values = item['values']
        
        # Lag redigeringsdialog (lignende som ny kunde, men forhåndsutfylt)
        dialog = tk.Toplevel(self.root)
        dialog.title("Rediger Kunde")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors['bg'])
        
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.LabelFrame(dialog, text="Kundeinformasjon", padding=20)
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        fields = {}
        
        ttk.Label(frame, text="Fornavn:").grid(row=0, column=0, sticky='w', pady=5)
        fields['fornavn'] = ttk.Entry(frame, width=25)
        fields['fornavn'].insert(0, values[1])
        fields['fornavn'].grid(row=0, column=1, pady=5, padx=(10, 0))
        
        ttk.Label(frame, text="Etternavn:").grid(row=1, column=0, sticky='w', pady=5)
        fields['etternavn'] = ttk.Entry(frame, width=25)
        fields['etternavn'].insert(0, values[2])
        fields['etternavn'].grid(row=1, column=1, pady=5, padx=(10, 0))
        
        ttk.Label(frame, text="Telefon:").grid(row=2, column=0, sticky='w', pady=5)
        fields['telefon'] = ttk.Entry(frame, width=25)
        fields['telefon'].insert(0, values[3])
        fields['telefon'].grid(row=2, column=1, pady=5, padx=(10, 0))
        
        ttk.Label(frame, text="E-post:").grid(row=3, column=0, sticky='w', pady=5)
        fields['epost'] = ttk.Entry(frame, width=25)
        fields['epost'].insert(0, values[4])
        fields['epost'].grid(row=3, column=1, pady=5, padx=(10, 0))
        
        ttk.Label(frame, text="Adresse:").grid(row=4, column=0, sticky='w', pady=5)
        fields['adresse'] = ttk.Entry(frame, width=25)
        fields['adresse'].insert(0, values[5])
        fields['adresse'].grid(row=4, column=1, pady=5, padx=(10, 0))
        
        button_frame = tk.Frame(frame, bg=self.colors['card_bg'])
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        def update_customer():
            if not fields['fornavn'].get() or not fields['etternavn'].get():
                messagebox.showerror("Feil", "Fornavn og etternavn er påkrevd!")
                return
                
            conn = self.get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    query = """UPDATE Kunder SET fornavn=%s, etternavn=%s, telefon=%s, epost=%s, adresse=%s 
                             WHERE kunde_id=%s"""
                    cursor.execute(query, (
                        fields['fornavn'].get(),
                        fields['etternavn'].get(),
                        fields['telefon'].get(),
                        fields['epost'].get(),
                        fields['adresse'].get(),
                        values[0]
                    ))
                    conn.commit()
                    messagebox.showinfo("Suksess", "Kunde oppdatert!")
                    dialog.destroy()
                    self.refresh_customers()
                except mysql.connector.Error as err:
                    messagebox.showerror("Feil", f"Kunne ikke oppdatere kunde: {err}")
                finally:
                    conn.close()
        
        ttk.Button(button_frame, text="Oppdater", command=update_customer, style='Primary.TButton').pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="Avbryt", command=dialog.destroy).pack(side='left')
        
    def delete_customer(self):
        """Slett valgt kunde"""
        selection = self.customers_tree.selection()
        if not selection:
            messagebox.showwarning("Advarsel", "Vennligst velg en kunde å slette.")
            return
            
        item = self.customers_tree.item(selection[0])
        kunde_id = item['values'][0]
        kunde_navn = f"{item['values'][1]} {item['values'][2]}"
        
        if messagebox.askyesno("Bekreft", f"Er du sikker på at du vil slette kunde {kunde_navn}?"):
            conn = self.get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM Kunder WHERE kunde_id = %s", (kunde_id,))
                    conn.commit()
                    messagebox.showinfo("Suksess", "Kunde slettet!")
                    self.refresh_customers()
                except mysql.connector.Error as err:
                    messagebox.showerror("Feil", f"Kunne ikke slette kunde: {err}")
                finally:
                    conn.close()
                    
    def refresh_appointments(self):
        """Oppdater avtaleliste"""
        for item in self.appointments_tree.get_children():
            self.appointments_tree.delete(item)
        
        conn = self.get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT a.avtale_id, CONCAT(k.fornavn, ' ', k.etternavn), a.dato, a.tidspunkt, a.tjeneste, a.status, a.kommentar
                    FROM Avtaler a
                    JOIN Kunder k ON a.kunde_id = k.kunde_id
                    ORDER BY a.dato DESC, a.tidspunkt DESC
                """)
                for row in cursor.fetchall():
                    self.appointments_tree.insert('', 'end', values=row)
            except mysql.connector.Error as err:
                messagebox.showerror("Feil", f"Kunne ikke hente avtaler: {err}")
            finally:
                conn.close()

    def new_appointment_dialog(self):
        messagebox.showinfo("Info", "Denne funksjonen er ikke implementert ennå.")

    def edit_appointment(self):
        selection = self.appointments_tree.selection()
        if not selection:
            messagebox.showwarning("Advarsel", "Vennligst velg en avtale å redigere.")
            return
        messagebox.showinfo("Info", "Redigering av avtale ikke implementert ennå.")
    def complete_appointment(self):
        selection = self.appointments_tree.selection()
        if not selection:
            messagebox.showwarning("Advarsel", "Velg en avtale å markere som fullført.")
            return
        
        avtale_id = self.appointments_tree.item(selection[0])['values'][0]
        
        conn = self.get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("UPDATE Avtaler SET status = 'Fullført' WHERE avtale_id = %s", (avtale_id,))
                conn.commit()
                messagebox.showinfo("Suksess", "Avtale markert som fullført.")
                self.refresh_appointments()
            except mysql.connector.Error as err:
                messagebox.showerror("Feil", f"Feil ved oppdatering: {err}")
            finally:
                conn.close()
    def cancel_appointment(self):
        selection = self.appointments_tree.selection()
        if not selection:
            messagebox.showwarning("Advarsel", "Velg en avtale å avlyse.")
            return
        
        avtale_id = self.appointments_tree.item(selection[0])['values'][0]
        
        if not messagebox.askyesno("Bekreft", "Er du sikker på at du vil avlyse denne avtalen?"):
            return
        
        conn = self.get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("UPDATE Avtaler SET status = 'Avlyst' WHERE avtale_id = %s", (avtale_id,))
                conn.commit()
                messagebox.showinfo("Avlyst", "Avtale er avlyst.")
                self.refresh_appointments()
            except mysql.connector.Error as err:
                messagebox.showerror("Feil", f"Feil ved oppdatering: {err}")
            finally:
                conn.close()
    def filter_appointments(self, event=None):
        status = self.appointment_filter.get()
        
        for item in self.appointments_tree.get_children():
            self.appointments_tree.delete(item)
        
        conn = self.get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                if status == 'Alle':
                    cursor.execute("""
                        SELECT a.avtale_id, CONCAT(k.fornavn, ' ', k.etternavn), a.dato, a.tidspunkt, a.tjeneste, a.status, a.kommentar
                        FROM Avtaler a
                        JOIN Kunder k ON a.kunde_id = k.kunde_id
                        ORDER BY a.dato DESC, a.tidspunkt DESC
                    """)
                else:
                    cursor.execute("""
                        SELECT a.avtale_id, CONCAT(k.fornavn, ' ', k.etternavn), a.dato, a.tidspunkt, a.tjeneste, a.status, a.kommentar
                        FROM Avtaler a
                        JOIN Kunder k ON a.kunde_id = k.kunde_id
                        WHERE a.status = %s
                        ORDER BY a.dato DESC, a.tidspunkt DESC
                    """, (status,))
                
                for row in cursor.fetchall():
                    self.appointments_tree.insert('', 'end', values=row)
            except mysql.connector.Error as err:
                messagebox.showerror("Feil", f"Kunne ikke filtrere avtaler: {err}")
            finally:
                conn.close()

    def new_product_dialog(self):
        messagebox.showinfo("Info", "Denne funksjonen er ikke implementert ennå.")
    
    def edit_product(self):
        messagebox.showinfo("Info", "Denne funksjonen er ikke implementert ennå.")

    def adjust_inventory(self):
        messagebox.showinfo("Info", "Denne funksjonen er ikke implementert ennå.")

    def delete_product(self):
        messagebox.showinfo("Info", "Denne funksjonen er ikke implementert ennå.")

    def filter_inventory(self, event=None):
        pass

    def new_employee_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Ny Ansatt")
        dialog.geometry("400x250")
        dialog.configure(bg=self.colors['bg'])
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.LabelFrame(dialog, text="Ansattinfo", padding=20)
        frame.pack(fill='both', expand=True, padx=20, pady=20)

        fields = {}

        ttk.Label(frame, text="Navn:").grid(row=0, column=0, sticky='w', pady=5)
        fields['navn'] = ttk.Entry(frame, width=25)
        fields['navn'].grid(row=0, column=1, pady=5, padx=(10, 0))

        ttk.Label(frame, text="Stilling:").grid(row=1, column=0, sticky='w', pady=5)
        fields['stilling'] = ttk.Entry(frame, width=25)
        fields['stilling'].grid(row=1, column=1, pady=5, padx=(10, 0))

        ttk.Label(frame, text="Telefon:").grid(row=2, column=0, sticky='w', pady=5)
        fields['telefon'] = ttk.Entry(frame, width=25)
        fields['telefon'].grid(row=2, column=1, pady=5, padx=(10, 0))

        ttk.Label(frame, text="E-post:").grid(row=3, column=0, sticky='w', pady=5)
        fields['epost'] = ttk.Entry(frame, width=25)
        fields['epost'].grid(row=3, column=1, pady=5, padx=(10, 0))

        def save_employee():
            if not fields['navn'].get():
                messagebox.showerror("Feil", "Navn er påkrevd!")
                return
            conn = self.get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    query = """INSERT INTO Ansatte (navn, stilling, telefon, epost)
                            VALUES (%s, %s, %s, %s)"""
                    cursor.execute(query, (
                        fields['navn'].get(),
                        fields['stilling'].get(),
                        fields['telefon'].get(),
                        fields['epost'].get()
                    ))
                    conn.commit()
                    messagebox.showinfo("Suksess", "Ansatt lagt til!")
                    dialog.destroy()
                    self.refresh_employees()
                except mysql.connector.Error as err:
                    messagebox.showerror("Feil", f"Kunne ikke lagre ansatt: {err}")
                finally:
                    conn.close()

        button_frame = tk.Frame(frame, bg=self.colors['card_bg'])
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="Lagre", command=save_employee, style='Primary.TButton').pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="Avbryt", command=dialog.destroy).pack(side='left')


    def edit_employee(self):
        selection = self.employees_tree.selection()
        if not selection:
            messagebox.showwarning("Advarsel", "Velg en ansatt å redigere.")
            return
        item = self.employees_tree.item(selection[0])
        values = item['values']
        dialog = tk.Toplevel(self.root)
        dialog.title("Rediger Ansatt")
        dialog.geometry("400x250")
        dialog.configure(bg=self.colors['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        frame = ttk.LabelFrame(dialog, text="Ansattinfo", padding=20)
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        fields = {}
        ttk.Label(frame, text="Navn:").grid(row=0, column=0, sticky='w', pady=5)
        fields['navn'] = ttk.Entry(frame, width=25)
        fields['navn'].insert(0, values[1])
        fields['navn'].grid(row=0, column=1, pady=5, padx=(10, 0))
        ttk.Label(frame, text="Stilling:").grid(row=1, column=0, sticky='w', pady=5)
        fields['stilling'] = ttk.Entry(frame, width=25)
        fields['stilling'].insert(0, values[2])
        fields['stilling'].grid(row=1, column=1, pady=5, padx=(10, 0))
        ttk.Label(frame, text="Telefon:").grid(row=2, column=0, sticky='w', pady=5)
        fields['telefon'] = ttk.Entry(frame, width=25)
        fields['telefon'].insert(0, values[3])
        fields['telefon'].grid(row=2, column=1, pady=5, padx=(10, 0))
        ttk.Label(frame, text="E-post:").grid(row=3, column=0, sticky='w', pady=5)
        fields['epost'] = ttk.Entry(frame, width=25)
        fields['epost'].insert(0, values[4])
        fields['epost'].grid(row=3, column=1, pady=5, padx=(10, 0))
        def update_employee():
            if not fields['navn'].get():
                messagebox.showerror("Feil", "Navn er påkrevd!")
                return
            conn = self.get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    query = """UPDATE Ansatte SET navn=%s, stilling=%s, telefon=%s, epost=%s
                           WHERE ansatt_id=%s"""
                    cursor.execute(query, (
                        fields['navn'].get(),
                        fields['stilling'].get(),
                        fields['telefon'].get(),
                        fields['epost'].get(),
                        values[0]
                    ))
                    conn.commit()
                    messagebox.showinfo("Suksess", "Ansatt oppdatert!")
                    dialog.destroy()
                    self.refresh_employees()
                except mysql.connector.Error as err:
                    messagebox.showerror("Feil", f"Kunne ikke oppdatere ansatt: {err}")
                finally:
                    conn.close()
        button_frame = tk.Frame(frame, bg=self.colors['card_bg'])
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="Oppdater", command=update_employee, style='Primary.TButton').pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="Avbryt", command=dialog.destroy).pack(side='left')

    def delete_employee(self):
        messagebox.showinfo("Info", "Denne funksjonen er ikke implementert ennå.")

    def refresh_employees(self):
        """Oppdater ansattliste"""
        for item in self.employees_tree.get_children():
            self.employees_tree.delete(item)
        conn = self.get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM Ansatte ORDER BY navn")
                for row in cursor.fetchall():
                    self.employees_tree.insert('', 'end', values=row)
            except mysql.connector.Error as err:
                messagebox.showerror("Feil", f"Kunne ikke hente ansatte: {err}")
            finally:
                conn.close()



if __name__ == "__main__":
    root = tk.Tk()
    app = HaarOgBlomsterApp(root)
    root.mainloop()
