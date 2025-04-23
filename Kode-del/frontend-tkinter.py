import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as msg
import mysql.connector
 
# --- KONFIGURASJON ---
HOST = "10.10.25.50"         # Din MySQL-vert
USER = "dennis"              # Ditt MySQL-brukernavn
PASSWORD = "dennis"       # Ditt MySQL-passord
DATABASE = "Skoleapplikasjon"      # Bruk databasen som er opprettet med SQL-koden din
 
def connect_db():
    """Oppretter en ny tilkobling til MySQL-databasen."""
    return mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DATABASE
    )
 
# --- Tabellstruktur definert i et oppslagsordbok ---
# Hver nøkkel er et tabellnavn, med tilhørende liste over felter,
# INSERT-spørring og SELECT-spørring.
tables = {
    "rolle": {
        "fields": ["rolle_navn"],
        "insert_query": "INSERT INTO rolle (rolle_navn) VALUES (%s)",
        "select_query": "SELECT * FROM rolle"
    },
    "brukere": {
        "fields": ["fornavn", "etternavn", "rolle_navn"],
        "insert_query": "INSERT INTO brukere (fornavn, etternavn, rolle_navn) VALUES (%s, %s, %s)",
        "select_query": "SELECT * FROM brukere"
    },
    "admin": {
        "fields": ["fornavn", "etternavn"],
        "insert_query": "INSERT INTO admin (fornavn, etternavn) VALUES (%s, %s)",
        "select_query": "SELECT * FROM admin"
    },
    "laerer": {
        "fields": ["fornavn", "etternavn", "fag", "alder"],
        "insert_query": "INSERT INTO laerer (fornavn, etternavn, fag, alder) VALUES (%s, %s, %s, %s)",
        "select_query": "SELECT * FROM laerer"
    },
    "elever": {
        "fields": ["fornavn", "etternavn", "trinn", "fodselsdato"],
        "insert_query": "INSERT INTO elever (fornavn, etternavn, trinn, fodselsdato) VALUES (%s, %s, %s, %s)",
        "select_query": "SELECT * FROM elever"
    },
    "fag": {
        "fields": ["fag_navn"],
        "insert_query": "INSERT INTO fag (fag_navn) VALUES (%s)",
        "select_query": "SELECT * FROM fag"
    },
    "elev_fag": {
        "fields": ["fornavn", "etternavn", "fag_navn", "karakter"],
        "insert_query": "INSERT INTO elev_fag (fornavn, etternavn, fag_navn, karakter) VALUES (%s, %s, %s, %s)",
        "select_query": "SELECT * FROM elev_fag"
    },
    "oppgaver": {
        "fields": ["fornavn", "etternavn", "oppgave_tekst", "fag_navn"],
        "insert_query": "INSERT INTO oppgaver (fornavn, etternavn, oppgave_tekst, fag_navn) VALUES (%s, %s, %s, %s)",
        "select_query": "SELECT * FROM oppgaver"
    },
    "fravaer": {
        "fields": ["fornavn", "etternavn", "dato", "antall_timer"],
        "insert_query": "INSERT INTO fravaer (fornavn, etternavn, dato, antall_timer) VALUES (%s, %s, %s, %s)",
        "select_query": "SELECT * FROM fravaer"
    },
    "klasse": {
        "fields": ["klasse_navn"],
        "insert_query": "INSERT INTO klasse (klasse_navn) VALUES (%s)",
        "select_query": "SELECT * FROM klasse"
    },
    "klasse_elev": {
        "fields": ["klasse_navn", "fornavn", "etternavn"],
        "insert_query": "INSERT INTO klasse_elev (klasse_navn, fornavn, etternavn) VALUES (%s, %s, %s)",
        "select_query": "SELECT * FROM klasse_elev"
    },
    "klasse_laerer": {
        "fields": ["klasse_navn", "fornavn", "etternavn"],
        "insert_query": "INSERT INTO klasse_laerer (klasse_navn, fornavn, etternavn) VALUES (%s, %s, %s)",
        "select_query": "SELECT * FROM klasse_laerer"
    },
    "kontroll": {
        "fields": ["fornavn", "etternavn", "beskrivelse", "dato"],
        "insert_query": "INSERT INTO kontroll (fornavn, etternavn, beskrivelse, dato) VALUES (%s, %s, %s, %s)",
        "select_query": "SELECT * FROM kontroll"
    },
    "devices": {
        "fields": ["fornavn", "etternavn", "device_type", "device_model"],
        "insert_query": "INSERT INTO devices (fornavn, etternavn, device_type, device_model) VALUES (%s, %s, %s, %s)",
        "select_query": "SELECT * FROM devices"
    },
    "postdata": {
        "fields": ["fornavn", "etternavn", "innhold", "tidspunkt"],
        "insert_query": "INSERT INTO postdata (fornavn, etternavn, innhold, tidspunkt) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)",
        "select_query": "SELECT * FROM postdata"
    },
    "start": {
        "fields": ["innstilling", "verdi"],
        "insert_query": "INSERT INTO start (innstilling, verdi) VALUES (%s, %s)",
        "select_query": "SELECT * FROM start"
    }
}

 
# --- Tkinter GUI-applikasjonen ---
root = tk.Tk()
root.title("Skoleapp Database")
 
# Funksjon: Oppdater inputfeltene basert på valgt tabell
def update_fields(event=None):
    # Fjern gamle widgets i entry_frame
    for widget in entry_frame.winfo_children():
        widget.destroy()
    selected_table = table_var.get()
    fields = tables[selected_table]["fields"]
    # Globalt oppslagsordbok for entry widgets
    global entry_widgets
    entry_widgets = {}
    row = 0
    for field in fields:
        lbl = tk.Label(entry_frame, text=f"{field}:")
        lbl.grid(row=row, column=0, padx=5, pady=5, sticky=tk.E)
        ent = tk.Entry(entry_frame, width=20)
        ent.grid(row=row, column=1, padx=5, pady=5)
        entry_widgets[field] = ent
        row += 1
 
# Funksjon: Legg til en post i den valgte tabellen
def add_record():
    selected_table = table_var.get()
    fields = tables[selected_table]["fields"]
    values = []
    for field in fields:
        value = entry_widgets[field].get().strip()
        if not value:
            msg.showwarning("Advarsel", f"Feltet '{field}' må fylles ut.")
            return
        values.append(value)
    try:
        conn = connect_db()
        cursor = conn.cursor()
        insert_query = tables[selected_table]["insert_query"]
        cursor.execute(insert_query, tuple(values))
        conn.commit()
    except Exception as e:
        msg.showerror("Feil", f"Kunne ikke legge til post:\n{e}")
        return
    finally:
        if conn:
            conn.close()
    # Tøm inputfeltene og oppdater listeboksen
    for ent in entry_widgets.values():
        ent.delete(0, tk.END)
    update_listbox()
 
# Funksjon: Hent ut og vis poster fra den valgte tabellen
def update_listbox():
    selected_table = table_var.get()
    try:
        conn = connect_db()
        cursor = conn.cursor()
        select_query = tables[selected_table]["select_query"]
        cursor.execute(select_query)
        rows = cursor.fetchall()
    except Exception as e:
        msg.showerror("Feil", f"Kunne ikke hente data:\n{e}")
        return
    finally:
        if conn:
            conn.close()
    listbox.delete(0, tk.END)
    for row in rows:
        listbox.insert(tk.END, row)
 
# --- GUI: Velg tabell ---
select_frame = tk.Frame(root)
select_frame.pack(pady=10)
lbl_table = tk.Label(select_frame, text="Velg tabell:")
lbl_table.pack(side=tk.LEFT, padx=5)
table_var = tk.StringVar()
table_combobox = ttk.Combobox(select_frame, textvariable=table_var, state="readonly")
table_combobox['values'] = list(tables.keys())
table_combobox.current(0)
table_combobox.pack(side=tk.LEFT, padx=5)
table_combobox.bind("<<ComboboxSelected>>", update_fields)
 
# --- GUI: Inndatafelt for valgt tabell ---
entry_frame = tk.Frame(root)
entry_frame.pack(pady=10)
entry_widgets = {}
update_fields()  # Initialiser inputfeltene for standard valgt tabell
 
# --- GUI: Knapper for å legge til post og oppdatere liste ---
button_frame = tk.Frame(root)
button_frame.pack(pady=10)
btn_add = tk.Button(button_frame, text="Legg til post", command=add_record)
btn_add.pack(side=tk.LEFT, padx=10)
btn_update = tk.Button(button_frame, text="Oppdater liste", command=update_listbox)
btn_update.pack(side=tk.LEFT, padx=10)
 
# --- GUI: Listeboks for å vise poster ---
listbox = tk.Listbox(root, width=80)
listbox.pack(padx=10, pady=10)
 
# Oppdater listeboksen ved oppstart
update_listbox()
 
root.mainloop()
 