import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as msg
import mysql.connector

# --- KONFIGURASJON ---
HOST = "192.168.1.8"
USER = "dennis"
PASSWORD = "dennis"
DATABASE = "Skoleapplikasjon"

def connect_db():
    return mysql.connector.connect(host=HOST, user=USER, password=PASSWORD, database=DATABASE)

# --- Tabellstruktur definert i et oppslagsordbok ---
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

# --- Tkinter GUI ---
root = tk.Tk()
root.title("Skoleapp Database")

def update_fields(event=None):
    for widget in entry_frame.winfo_children():
        widget.destroy()
    
    selected_table = table_var.get()
    if selected_table not in tables:
        return

    fields = tables[selected_table]["fields"]
    global entry_widgets
    entry_widgets = {}

    for row, field in enumerate(fields):
        tk.Label(entry_frame, text=f"{field}:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.E)
        ent = tk.Entry(entry_frame, width=20)
        ent.grid(row=row, column=1, padx=5, pady=5)
        entry_widgets[field] = ent

def add_record():
    selected_table = table_var.get()
    if selected_table not in tables:
        return

    fields = tables[selected_table]["fields"]
    values = [entry_widgets[field].get().strip() for field in fields]
    
    if "" in values:
        msg.showwarning("Advarsel", "Alle felt må fylles ut.")
        return
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(tables[selected_table]["insert_query"], tuple(values))
        conn.commit()
    except Exception as e:
        msg.showerror("Feil", f"Kunne ikke legge til post: {e}")
    finally:
        conn.close()

    update_listbox()
    for ent in entry_widgets.values():
        ent.delete(0, tk.END)

def update_listbox():
    global tables  # Sikrer at funksjonen finner tabellen
    listbox.delete(0, tk.END)
    
    print("tables keys:", list(tables.keys()))  # Debugging for å sjekke at tables eksisterer

    try:
        conn = connect_db()
        cursor = conn.cursor()
        for table in tables.keys():
            cursor.execute(tables[table]["select_query"])
            for row in cursor.fetchall():
                listbox.insert(tk.END, (table, *row))
    except Exception as e:
        msg.showerror("Feil", f"Kunne ikke hente data: {e}")
    finally:
        conn.close()

def delete_selected():
    selected_indices = listbox.curselection()
    if not selected_indices:
        msg.showwarning("Advarsel", "Velg minst én rad for å slette.")
        return
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        for index in selected_indices:
            data = listbox.get(index)
            table = data[0]
            primary_key_field = tables[table]["fields"][0]
            delete_query = f"DELETE FROM {table} WHERE {primary_key_field} = %s"
            cursor.execute(delete_query, (data[1],))

        conn.commit()
    except Exception as e:
        msg.showerror("Feil", f"Kunne ikke slette post: {e}")
    finally:
        conn.close()
    
    update_listbox()

# --- GUI Elementer ---
select_frame = tk.Frame(root)
select_frame.pack(pady=10)

tk.Label(select_frame, text="Velg tabell:").pack(side=tk.LEFT, padx=5)

table_var = tk.StringVar()
table_combobox = ttk.Combobox(select_frame, textvariable=table_var, state="readonly")
table_combobox['values'] = list(tables.keys())  # Sikrer at tables eksisterer
table_combobox.pack(side=tk.LEFT, padx=5)
table_combobox.bind("<<ComboboxSelected>>", update_fields)

entry_frame = tk.Frame(root)
entry_frame.pack(pady=10)
update_fields()

button_frame = tk.Frame(root)
button_frame.pack(pady=10)

tk.Button(button_frame, text="Legg til post", command=add_record).pack(side=tk.LEFT, padx=10)
tk.Button(button_frame, text="Slett valgte", command=delete_selected).pack(side=tk.LEFT, padx=10)
tk.Button(button_frame, text="Oppdater liste", command=update_listbox).pack(side=tk.LEFT, padx=10)

listbox = tk.Listbox(root, width=80, selectmode=tk.EXTENDED)
listbox.pack(padx=10, pady=10)

update_listbox()  # Flyttet hit for å sikre at GUI er lastet først

root.mainloop()
