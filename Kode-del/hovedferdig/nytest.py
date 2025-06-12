import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
import mysql.connector
from mysql.connector import Error
import webbrowser
from PIL import Image, ImageTk
import io
import base64

class HaarOgBlomsterApp:
    def __init__(self, root):
        """
        Hovedklasse for Hår og Blomster applikasjonen
        Initialiserer hovedvinduet og setter opp GUI-komponenter
        """
        self.root = root
        self.root.title("Hår og Blomster - Database Manager")
        self.root.state('zoomed')  # Fulskjerm på Windows
        
        # Variabler for responsivt design
        self.burger_menu_open = False
        self.current_page = "home"
        
        # Database konfigurasjon (basert på din test-kode)
        self.db_config = {
            'host': "10.10.25.55",
            'user': "dennis", 
            'password': "r6dexMHMNE",
            'database': "HaarOgBlomster"
        }
        
        # Fargepalett for applikasjonen
        self.colors = {
            'primary': '#2C3E50',      # Mørk blå
            'secondary': '#3498DB',     # Lys blå
            'accent': '#E74C3C',        # Rød
            'background': '#ECF0F1',    # Lys grå
            'text': '#2C3E50',          # Mørk blå tekst
            'white': '#FFFFFF'
        }
        
        self.setup_styles()
        self.create_main_layout()
        self.create_navigation_bar()
        self.create_main_content()
        self.create_footer()
        self.show_home_page()
        
        # Responsivt design - oppdaterer layout ved vindusendring
        self.root.bind('<Configure>', self.on_window_resize)
    
    def setup_styles(self):
        """
        Setter opp ttk styles for konsistent design
        """
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Konfigurasjon av forskjellige ttk-elementer
        self.style.configure('Navigation.TFrame', background=self.colors['primary'])
        self.style.configure('Content.TFrame', background=self.colors['background'])
        self.style.configure('Footer.TFrame', background=self.colors['primary'])
        
        # Knapp-stiler
        self.style.configure('Primary.TButton', 
                           background=self.colors['secondary'],
                           foreground=self.colors['white'],
                           font=('Arial', 12, 'bold'))
        
        self.style.configure('Accent.TButton',
                           background=self.colors['accent'],
                           foreground=self.colors['white'],
                           font=('Arial', 10))
    
    def create_main_layout(self):
        """
        Oppretter hovedlayouten med tre hovedseksjoner:
        - Navigasjonsbar øverst
        - Hovedinnhold i midten  
        - Footer nederst
        """
        # Hovedcontainer som fyller hele vinduet
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Navigasjonsbar (fast høyde)
        self.nav_frame = ttk.Frame(self.main_container, style='Navigation.TFrame', height=60)
        self.nav_frame.pack(fill=tk.X, side=tk.TOP)
        self.nav_frame.pack_propagate(False)  # Forhindrer at rammen endrer størrelse
        
        # Hovedinnholdsområde (ekspanderer)
        self.content_frame = ttk.Frame(self.main_container, style='Content.TFrame')
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Footer (fast høyde)
        self.footer_frame = ttk.Frame(self.main_container, style='Footer.TFrame', height=80)
        self.footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.footer_frame.pack_propagate(False)
    
    def create_navigation_bar(self):
        """
        Oppretter navigasjonsbaren med:
        - Burger-meny til venstre
        - Tittel i midten
        - Kontakt-knapp til høyre
        """
        # Burger-meny knapp (venstre side)
        self.burger_btn = tk.Button(self.nav_frame, 
                                   text="☰", 
                                   font=('Arial', 20),
                                   bg=self.colors['primary'],
                                   fg=self.colors['white'],
                                   border=0,
                                   command=self.toggle_burger_menu)
        self.burger_btn.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Hovedtittel (midten)
        self.title_label = tk.Label(self.nav_frame,
                                   text="Hår og Blomster",
                                   font=('Arial', 24, 'bold'),
                                   bg=self.colors['primary'],
                                   fg=self.colors['white'])
        self.title_label.pack(side=tk.LEFT, expand=True)
        
        # Kontakt-knapp (høyre side)
        self.contact_btn = tk.Button(self.nav_frame,
                                    text="Kontakt",
                                    font=('Arial', 12),
                                    bg=self.colors['accent'],
                                    fg=self.colors['white'],
                                    border=0,
                                    padx=20,
                                    command=self.show_contact_info)
        self.contact_btn.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # Burger-meny dropdown (skjult som standard)
        self.create_burger_menu()
    
    def create_burger_menu(self):
        """
        Lager dropdown-menyen som vises når burger-knappen trykkes
        Inneholder liste over databse-tabeller
        """
        self.burger_menu = tk.Frame(self.main_container, bg=self.colors['white'], relief=tk.RAISED, bd=2)
        
        # Henter tabellnavn fra databasen
        tables = self.get_database_tables()
        
        # Legger til menyalternativer
        menu_items = [
            ("🏠 Hjem", lambda: self.navigate_to('home')),
            ("📊 Tabelloversikt", lambda: self.navigate_to('tables')),
            ("─────────", None),  # Skillelinje
        ]
        
        # Legger til databse-tabeller i menyen
        for table in tables:
            menu_items.append((f"📋 {table}", lambda t=table: self.navigate_to('table', t)))
        
        # Oppretter menyknapper
        for text, command in menu_items:
            if command is None:  # Skillelinje
                separator = tk.Label(self.burger_menu, text=text, bg=self.colors['white'], fg=self.colors['text'])
                separator.pack(fill=tk.X, pady=2)
            else:
                btn = tk.Button(self.burger_menu,
                               text=text,
                               font=('Arial', 11),
                               bg=self.colors['white'],
                               fg=self.colors['text'],
                               border=0,
                               anchor='w',
                               padx=15,
                               pady=8,
                               command=command)
                btn.pack(fill=tk.X)
                # Hover-effekt
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.colors['background']))
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.colors['white']))
    
    def get_database_tables(self):
        """
        Henter liste over tabeller fra databasen
        Returnerer tom liste hvis tilkobling feiler
        """
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            connection.close()
            return tables
        except Error as e:
            print(f"Feil ved henting av tabeller: {e}")
            return ["Kunde", "Bestilling", "Produkt"]  # Fallback-tabeller
    
    def toggle_burger_menu(self):
        """
        Viser/skjuler burger-menyen
        """
        if self.burger_menu_open:
            self.burger_menu.place_forget()
            self.burger_menu_open = False
        else:
            # Posisjonerer menyen under burger-knappen
            self.burger_menu.place(x=10, y=70, width=250)
            self.burger_menu_open = True
    
    def create_main_content(self):
        """
        Oppretter hovedinnholdsområdet hvor forskjellige sider vises
        """
        # Canvas for scrolling (hvis nødvendig)
        self.content_canvas = tk.Canvas(self.content_frame, bg=self.colors['background'])
        self.content_scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=self.content_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.content_canvas, style='Content.TFrame')
        
        # Konfigurerer scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))
        )
        
        self.content_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.content_canvas.configure(yscrollcommand=self.content_scrollbar.set)
        
        # Plasserer canvas og scrollbar
        self.content_canvas.pack(side="left", fill="both", expand=True)
        self.content_scrollbar.pack(side="right", fill="y")
    
    def create_footer(self):
        """
        Oppretter footer med kontaktinformasjon og copyright
        """
        # Kontaktinformasjon til venstre
        contact_info = tk.Label(self.footer_frame,
                               text="📞 +47 123 45 678 | ✉️ post@haarogblomster.no | 📍 Oslo, Norge",
                               font=('Arial', 10),
                               bg=self.colors['primary'],
                               fg=self.colors['white'])
        contact_info.pack(side=tk.LEFT, padx=20, pady=25)
        
        # Copyright til høyre
        copyright_info = tk.Label(self.footer_frame,
                                 text="© 2024 Hår og Blomster AS. Alle rettigheter forbeholdt.",
                                 font=('Arial', 10),
                                 bg=self.colors['primary'],
                                 fg=self.colors['white'])
        copyright_info.pack(side=tk.RIGHT, padx=20, pady=25)
    
    def clear_content(self):
        """
        Fjerner alt innhold fra hovedområdet
        """
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
    
    def show_home_page(self):
        """
        Viser startsiden med velkomstmelding og bakgrunnsbilde
        """
        self.clear_content()
        self.current_page = "home"
        
        # Hovedcontainer for startsiden
        home_container = ttk.Frame(self.scrollable_frame, style='Content.TFrame')
        home_container.pack(fill=tk.BOTH, expand=True, padx=50, pady=50)
        
        # Stor velkomsttekst
        welcome_title = tk.Label(home_container,
                                text="Velkommen til Hår og Blomster",
                                font=('Arial', 36, 'bold'),
                                bg=self.colors['background'],
                                fg=self.colors['primary'])
        welcome_title.pack(pady=(0, 20))
        
        # Undertekst
        subtitle = tk.Label(home_container,
                           text="Din komplette løsning for database-administrasjon",
                           font=('Arial', 18),
                           bg=self.colors['background'],
                           fg=self.colors['text'])
        subtitle.pack(pady=(0, 40))
        
        # Bakgrunnsbilde-placeholder (erstatt med echt bilde)
        image_frame = tk.Frame(home_container, bg=self.colors['secondary'], height=300, width=600)
        image_frame.pack(pady=20)
        image_frame.pack_propagate(False)
        
        image_placeholder = tk.Label(image_frame,
                                    text="🌸 Hår og Blomster 🌸\n\nVakkert bakgrunnsbilde kommer her\n\n(Legg til din egen bildefil)",
                                    font=('Arial', 16),
                                    bg=self.colors['secondary'],
                                    fg=self.colors['white'],
                                    justify=tk.CENTER)
        image_placeholder.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Hovedknapp for å gå til tabeller
        main_button = tk.Button(home_container,
                               text="Utforsk Database Tabeller",
                               font=('Arial', 16, 'bold'),
                               bg=self.colors['accent'],
                               fg=self.colors['white'],
                               padx=40,
                               pady=15,
                               border=0,
                               command=lambda: self.navigate_to('tables'))
        main_button.pack(pady=30)
        
        # Hover-effekt for hovedknappen
        def on_enter(e):
            main_button.config(bg='#C0392B')  # Mørkere rød
        def on_leave(e):
            main_button.config(bg=self.colors['accent'])
        
        main_button.bind("<Enter>", on_enter)
        main_button.bind("<Leave>", on_leave)
    
    def show_tables_overview(self):
        """
        Viser oversikt over alle databse-tabeller
        """
        self.clear_content()
        self.current_page = "tables"
        
        # Tittel for tabelloversikt
        title = tk.Label(self.scrollable_frame,
                        text="Database Tabeller",
                        font=('Arial', 28, 'bold'),
                        bg=self.colors['background'],
                        fg=self.colors['primary'])
        title.pack(pady=30)
        
        # Henter tabeller fra database
        tables = self.get_database_tables()
        
        if not tables:
            no_tables_label = tk.Label(self.scrollable_frame,
                                      text="Ingen tabeller funnet eller databasefeil",
                                      font=('Arial', 14),
                                      bg=self.colors['background'],
                                      fg=self.colors['accent'])
            no_tables_label.pack(pady=20)
            return
        
        # Container for tabellkort
        tables_container = ttk.Frame(self.scrollable_frame, style='Content.TFrame')
        tables_container.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)
        
        # Lager kort for hver tabell
        for i, table in enumerate(tables):
            # Beregner grid-posisjon (3 kolonner)
            row = i // 3
            col = i % 3
            
            # Tabellkort
            table_card = tk.Frame(tables_container, 
                                 bg=self.colors['white'], 
                                 relief=tk.RAISED, 
                                 bd=2,
                                 padx=20, 
                                 pady=20)
            table_card.grid(row=row, column=col, padx=15, pady=15, sticky='ew')
            
            # Tabellnavn
            table_name = tk.Label(table_card,
                                 text=f"📋 {table}",
                                 font=('Arial', 16, 'bold'),
                                 bg=self.colors['white'],
                                 fg=self.colors['primary'])
            table_name.pack()
            
            # Beskrivelse (placeholder)
            description = tk.Label(table_card,
                                  text="Klikk for å se tabelldata",
                                  font=('Arial', 11),
                                  bg=self.colors['white'],
                                  fg=self.colors['text'])
            description.pack(pady=(5, 15))
            
            # Knapp for å åpne tabell
            open_btn = tk.Button(table_card,
                                text="Åpne tabell",
                                font=('Arial', 12),
                                bg=self.colors['secondary'],
                                fg=self.colors['white'],
                                border=0,
                                padx=20,
                                pady=8,
                                command=lambda t=table: self.navigate_to('table', t))
            open_btn.pack()
        
        # Gjør kolonnene like brede
        for i in range(3):
            tables_container.grid_columnconfigure(i, weight=1)
    
    def show_table_data(self, table_name):
        """
        Viser data fra en spesifikk database-tabell
        """
        self.clear_content()
        self.current_page = f"table_{table_name}"
        
        # Tittel
        title = tk.Label(self.scrollable_frame,
                        text=f"Tabell: {table_name}",
                        font=('Arial', 24, 'bold'),
                        bg=self.colors['background'],
                        fg=self.colors['primary'])
        title.pack(pady=20)
        
        # Tilbake-knapp
        back_btn = tk.Button(self.scrollable_frame,
                            text="← Tilbake til oversikt",
                            font=('Arial', 12),
                            bg=self.colors['primary'],
                            fg=self.colors['white'],
                            border=0,
                            padx=15,
                            pady=8,
                            command=lambda: self.navigate_to('tables'))
        back_btn.pack(anchor='w', padx=50, pady=(0, 20))
        
        try:
            # Kobler til database og henter data
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            
            # Henter kolonnenavn
            cursor.execute(f"DESCRIBE {table_name}")
            columns = [column[0] for column in cursor.fetchall()]
            
            # Henter data (begrenset til 100 rader for ytelse)
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
            data = cursor.fetchall()
            
            connection.close()
            
            # Treeview for tabellvisning
            tree_frame = ttk.Frame(self.scrollable_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)
            
            tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
            
            # Setter opp kolonner
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=120)
            
            # Legger til data
            for row in data:
                tree.insert('', tk.END, values=row)
            
            # Scrollbars for tabellen
            v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=tree.xview)
            tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            # Plasserer Treeview og scrollbars
            tree.grid(row=0, column=0, sticky='nsew')
            v_scrollbar.grid(row=0, column=1, sticky='ns')
            h_scrollbar.grid(row=1, column=0, sticky='ew')
            
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)
            
            # Informasjon om antall rader
            info_label = tk.Label(self.scrollable_frame,
                                 text=f"Viser {len(data)} rader fra {table_name} tabellen",
                                 font=('Arial', 11),
                                 bg=self.colors['background'],
                                 fg=self.colors['text'])
            info_label.pack(pady=10)
            
        except Error as e:
            # Feilhåndtering
            error_label = tk.Label(self.scrollable_frame,
                                  text=f"Feil ved lasting av tabell:\n{str(e)}",
                                  font=('Arial', 12),
                                  bg=self.colors['background'],
                                  fg=self.colors['accent'],
                                  justify=tk.CENTER)
            error_label.pack(pady=50)
    
    def navigate_to(self, page, parameter=None):
        """
        Navigasjonsfunksjon som bytte mellom forskjellige sider
        """
        # Lukker burger-meny hvis den er åpen
        if self.burger_menu_open:
            self.toggle_burger_menu()
        
        if page == 'home':
            self.show_home_page()
        elif page == 'tables':
            self.show_tables_overview()
        elif page == 'table' and parameter:
            self.show_table_data(parameter)
    
    def show_contact_info(self):
        """
        Viser kontaktinformasjon i en popup
        """
        messagebox.showinfo("Kontaktinformasjon", 
                           "Hår og Blomster AS\n\n"
                           "📞 Telefon: +47 123 45 678\n"
                           "✉️ E-post: post@haarogblomster.no\n"
                           "📍 Adresse: Oslo, Norge\n"
                           "🌐 Nettside: www.haarogblomster.no\n\n"
                           "Vi er tilgjengelige mandag-fredag 08:00-16:00")
    
    def on_window_resize(self, event):
        """
        Håndterer vindusendringer for responsivt design
        """
        if event.widget == self.root:
            # Oppdaterer canvas størrelse
            self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))
            
            # Skjuler burger-meny hvis vinduet endres
            if self.burger_menu_open:
                self.toggle_burger_menu()

def main():
    """
    Hovedfunksjon som starter applikasjonen
    """
    root = tk.Tk()
    app = HaarOgBlomsterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()