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
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        is_mobile = sw < 800
        root.geometry(f"{sw}x{sh}" if is_mobile else "300x200")
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
        pwd = self.password_entry.get().strip()
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
                                   "Du har ikke konfigurert 2FA enda.\n\nVil du konfigurere nå?"):
                new_secret = pyotp.random_base32()
                db_manager.execute_query("UPDATE brukere SET mfa_secret=%s WHERE epost=%s",
                                         (new_secret, user), commit=True)
                uri = pyotp.TOTP(new_secret).provisioning_uri(name=user, issuer_name="Skoleapplikasjon")
                qr_img = qrcode.make(uri)
                win = tk.Toplevel(self.root)
                win.title("Konfigurer 2FA")
                win.geometry("300x350")
                ttk.Label(win, text="Skann denne QR-koden\nmed Microsoft Authenticator:",
                          font=("Arial", 12), justify="center").pack(pady=10)
                tk_img = ImageTk.PhotoImage(qr_img)
                lbl = tk.Label(win, image=tk_img); lbl.image = tk_img; lbl.pack(pady=10)
                ttk.Button(win, text="Ferdig", command=win.destroy).pack(pady=(0,10))
            return
        code = simpledialog.askstring("2FA", "Skriv inn 6-sifret kode fra Authenticator:", parent=self.root)
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
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        self.is_mobile = sw < 800
        root.geometry(f"{sw}x{sh}" if self.is_mobile else "1400x800")
        if self.is_mobile: root.attributes('-fullscreen', True)
        root.title(f"Skole DB – {self.current_user} ({self.user_role})")
        root.configure(bg='#f0f8ff')

        self.base_font = ("Arial", 14 if self.is_mobile else 10)
        self.entry_w = 40 if self.is_mobile else 30
        self.combo_w = 40 if self.is_mobile else 30
        self.pad = 5 if self.is_mobile else 10

        style = ttk.Style(); style.theme_use('clam')
        style.configure("TButton", font=self.base_font, padding=self.pad)
        style.map("TButton", background=[("active", "#2980b9")])
        style.configure("TLabel", background='#f0f8ff', foreground='#2c3e50', font=self.base_font)
        style.configure("TEntry", font=self.base_font)
        style.configure("TFrame", background='#f0f8ff')
        style.configure("TLabelFrame", background='#dfe6e9', foreground='#2c3e50',
                        font=self.base_font + ("bold",))
        style.configure("Treeview", font=self.base_font)
        style.configure("Treeview.Heading", background='#3498db', foreground='white',
                        font=self.base_font + ("bold",))

        # Tabellkonfigurasjon
        self.tables = {
            "admin": {"fields":["epost"], "insert_query":"INSERT INTO admin (epost) VALUES (%s)", "select_query":"SELECT * FROM admin",
                      "foreign_keys":{"epost":{"table":"brukere","display_fields":["epost"]}}},
            "brukere": {"fields":["fornavn","etternavn","rolle_navn","epost","passord"],
                        "insert_query":"INSERT INTO brukere (fornavn,etternavn,rolle_navn,epost,passord) VALUES (%s,%s,%s,%s,%s)",
                        "select_query":"SELECT fornavn,etternavn,rolle_navn,epost,passord FROM brukere",
                        "foreign_keys":{"rolle_navn":{"table":"rolle","display_fields":["rolle_navn"]}}},
            "devices": {"fields":["epost","device_type","device_model"],
                        "insert_query":"INSERT INTO devices (epost,device_type,device_model) VALUES (%s,%s,%s)",
                        "select_query":"SELECT * FROM devices",
                        "foreign_keys":{"epost":{"table":"brukere","display_fields":["epost"]}}},
            "elever": {"fields":["epost","trinn","født"],
                       "insert_query":"INSERT INTO elever (epost,trinn,født) VALUES (%s,%s,%s)",
                       "select_query":"SELECT epost,trinn,født FROM elever",
                       "foreign_keys":{"epost":{"table":"brukere","display_fields":["epost"]},
                                      "trinn":{"table":"klasse","display_fields":["trinn"]}}},
            "elev_fag": {"fields":["epost","fag_navn","karakter"],
                         "insert_query":"INSERT INTO elev_fag (epost,fag_navn,karakter) VALUES (%s,%s,%s)",
                         "select_query":"SELECT * FROM elev_fag",
                         "foreign_keys":{"epost":{"table":"brukere","display_fields":["epost"]},
                                        "fag_navn":{"table":"fag","display_fields":["fag_navn"]}}},
            "fag": {"fields":["fag_navn"], "insert_query":"INSERT INTO fag (fag_navn) VALUES (%s)", "select_query":"SELECT * FROM fag"},
            "fravaer": {"fields":["epost","dato","antall_timer"],
                        "insert_query":"INSERT INTO fravaer (epost,dato,antall_timer) VALUES (%s,%s,%s)",
                        "select_query":"SELECT * FROM fravaer",
                        "foreign_keys":{"epost":{"table":"brukere","display_fields":["epost"]}}},
            "klasse": {"fields":["trinn"], "insert_query":"INSERT INTO klasse (trinn) VALUES (%s)", "select_query":"SELECT * FROM klasse"},
            "klasse_elev": {"fields":["klasse_navn","epost"],
                            "insert_query":"INSERT INTO klasse_elev (klasse_navn,epost) VALUES (%s,%s)",
                            "select_query":"SELECT * FROM klasse_elev",
                            "foreign_keys":{"klasse_navn":{"table":"klasse","display_fields":["klasse_navn"]},
                                           "epost":{"table":"brukere","display_fields":["epost"]}}},
            "klasse_laerer": {"fields":["klasse_navn","epost"],
                              "insert_query":"INSERT INTO klasse_laerer (klasse_navn,epost) VALUES (%s,%s)",
                              "select_query":"SELECT * FROM klasse_laerer",
                              "foreign_keys":{"klasse_navn":{"table":"klasse","display_fields":["klasse_navn"]},
                                             "epost":{"table":"brukere","display_fields":["epost"]}}},
            "kontroll": {"fields":["epost","beskrivelse","dato"],
                         "insert_query":"INSERT INTO kontroll (epost,beskrivelse,dato) VALUES (%s,%s,%s)",
                         "select_query":"SELECT * FROM kontroll",
                         "foreign_keys":{"epost":{"table":"brukere","display_fields":["epost"]}}},
            "laerer": {"fields":["epost","fag","alder"],
                       "insert_query":"INSERT INTO laerer (epost,fag,alder) VALUES (%s,%s,%s)",
                       "select_query":"SELECT * FROM laerer",
                       "foreign_keys":{"epost":{"table":"brukere","display_fields":["epost"]},
                                      "fag":{"table":"fag","display_fields":["fag_navn"]}}},
            "oppgaver": {"fields":["epost","oppgave_tekst","fag_navn"],
                         "insert_query":"INSERT INTO oppgaver (epost,oppgave_tekst,fag_navn) VALUES (%s,%s,%s)",
                         "select_query":"SELECT * FROM oppgaver",
                         "foreign_keys":{"epost":{"table":"brukere","display_fields":["epost"]},
                                        "fag_navn":{"table":"fag","display_fields":["fag_navn"]}}},
            "postdata": {"fields":["epost","innhold","tidspunkt"],
                         "insert_query":"INSERT INTO postdata (epost,innhold,tidspunkt) VALUES (%s,%s,%s)",
                         "select_query":"SELECT * FROM postdata",
                         "foreign_keys":{"epost":{"table":"brukere","display_fields":["epost"]}}},
            "rolle": {"fields":["rolle_navn"], "insert_query":"INSERT INTO rolle (rolle_navn) VALUES (%s)", "select_query":"SELECT * FROM rolle"},
            "start": {"fields":["innstilling","verdi"], "insert_query":"INSERT INTO start (innstilling,verdi) VALUES (%s,%s)", "select_query":"SELECT * FROM start"}
        }

        self.create_main_layout()

    def create_main_layout(self):
        # Header
        header = tk.Frame(self.root, bg='#2980b9')
        header.pack(fill=tk.X, pady=(0,self.pad))
        tk.Label(header, text="Skole Database Administrasjon",
                 bg='#2980b9', fg='white',
                 font=("Arial",24 if self.is_mobile else 20,"bold")).pack(side=tk.LEFT,padx=self.pad)
        tk.Label(header, text=f"Innlogget som: {self.current_user}",
                 bg='#2980b9', fg='white',
                 font=self.base_font).pack(side=tk.RIGHT,padx=self.pad)
        ttk.Button(header, text="Logg ut", command=self.logout).pack(side=tk.RIGHT,padx=self.pad)

        # Meny
        menu = tk.Frame(self.root, bg='#f0f8ff')
        menu.pack(fill=tk.X,pady=self.pad)
        tk.Label(menu, text="Tabell:", bg='#f0f8ff').pack(side=tk.LEFT,padx=(self.pad,0))
        tables = list(self.tables.keys())
        if self.user_role=='elev':
            tables = [t for t,v in self.tables.items() if 'epost' in v['fields']]
        self.table_var = tk.StringVar()
        self.table_dropdown = ttk.Combobox(menu,textvariable=self.table_var,values=tables,
                                           state="readonly",width=self.combo_w)
        self.table_dropdown.pack(side=tk.LEFT,padx=self.pad)
        self.table_dropdown.bind("<<ComboboxSelected>>",self.on_table_select)
        tk.Label(menu, text="Søk:", bg='#f0f8ff').pack(side=tk.LEFT,padx=(self.pad,0))
        self.search_entry = tk.Entry(menu, width=self.entry_w, font=self.base_font)
        self.search_entry.pack(side=tk.LEFT,fill=tk.X,expand=True,padx=self.pad)
        self.search_entry.bind('<KeyRelease>',self.perform_search)
        tk.Label(menu, text="Sorter etter:", bg='#f0f8ff').pack(side=tk.LEFT,padx=(self.pad,0))
        self.sort_var = tk.StringVar()
        self.sort_combobox = ttk.Combobox(menu,textvariable=self.sort_var,
                                          state="readonly",width=self.combo_w)
        self.sort_combobox.pack(side=tk.LEFT,padx=self.pad)
        ttk.Button(menu, text="Sorter", command=self.sort_results).pack(side=tk.LEFT,padx=self.pad)

        # Paneler 50/50
        if not self.is_mobile:
            left = tk.Frame(self.root, bg='#f0f8ff')
            left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=self.pad, pady=self.pad)
            right = tk.Frame(self.root, bg='#f0f8ff')
            right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=self.pad, pady=self.pad)

            # Venstre: data entry + detaljer
            if self.user_role!='elev':
                self.data_entry_frame = ttk.LabelFrame(left, text="Legg til/Endre")
                self.data_entry_frame.pack(fill=tk.X,pady=self.pad)
            else:
                self.data_entry_frame = None
            self.build_data_entry()
            details = ttk.LabelFrame(left, text="Detaljer")
            details.pack(fill=tk.BOTH,expand=True,pady=self.pad)
            self.details_text = tk.Text(details, state='disabled', wrap='word', font=self.base_font)
            self.details_text.pack(fill=tk.BOTH,expand=True,padx=self.pad,pady=self.pad)

            # Høyre: resultater + knapper
            self.build_results(right)

        else:
            # Mobil: stablet
            if self.user_role!='elev':
                self.data_entry_frame = ttk.LabelFrame(self.root, text="Legg til/Endre")
                self.data_entry_frame.pack(fill=tk.X,padx=self.pad,pady=self.pad)
            else:
                self.data_entry_frame = None
            self.build_data_entry()
            details = ttk.LabelFrame(self.root, text="Detaljer")
            details.pack(fill=tk.X,padx=self.pad,pady=self.pad)
            self.details_text = tk.Text(details, height=5, state='disabled', wrap='word', font=self.base_font)
            self.details_text.pack(fill=tk.X,padx=self.pad,pady=self.pad)
            self.build_results(self.root)

        # Status
        self.status_var = tk.StringVar("Velg en tabell for å starte...")
        status = tk.Label(self.root, textvariable=self.status_var, bd=1,relief=tk.SUNKEN,
                          anchor='w', font=self.base_font, bg='white', fg='#2c3e50')
        status.pack(side=tk.BOTTOM,fill=tk.X)

    def build_data_entry(self):
        if not self.data_entry_frame: return
        for w in self.data_entry_frame.winfo_children(): w.destroy()
        self.entry_widgets={}
        tbl = self.table_var.get(); info = self.tables.get(tbl,{})
        fks = info.get('foreign_keys',{})
        for field in info.get('fields',[]):
            if tbl=='brukere' and field=='passord' and self.user_role!='admin': continue
            frm = tk.Frame(self.data_entry_frame,bg='#dfe6e9'); frm.pack(fill=tk.X,padx=self.pad,pady=2)
            tk.Label(frm,text=f"{field}:",width=12,anchor='w',
                     bg='#dfe6e9',font=self.base_font).pack(side=tk.LEFT)
            if field in fks:
                ref= fks[field]; rinfo=self.tables[ref['table']]
                data=db_manager.execute_query(rinfo['select_query']) or []
                idxs=[rinfo['fields'].index(df) for df in ref['display_fields']]
                vals=sorted({" ".join(str(row[i]) for i in idxs) for row in data})
                ent=ttk.Combobox(frm,values=vals,state='readonly',font=self.base_font,width=self.combo_w)
            else:
                ent=tk.Entry(frm,font=self.base_font,width=self.entry_w)
            ent.pack(side=tk.LEFT,fill=tk.X,expand=True)
            self.entry_widgets[field]=ent

    def build_results(self,parent):
        tree = ttk.Treeview(parent,selectmode='browse')
        tree.pack(fill=tk.BOTH,expand=True)
        scroll=ttk.Scrollbar(parent,orient=tk.VERTICAL,command=tree.yview)
        scroll.pack(side=tk.RIGHT,fill=tk.Y)
        tree.configure(yscroll=scroll.set)
        tree.bind("<<TreeviewSelect>>",self.on_result_select)
        self.results_tree=tree

        action=tk.Frame(parent,bg='#f0f8ff'); action.pack(fill=tk.X,pady=self.pad)
        btns=[]
        if self.user_role!='elev':
            btns=[("Legg til",self.add_record),("Rediger",self.populate_form_for_selected),
                  ("Oppdater post",self.update_selected_record),("Oppdater alle",self.update_all_records),
                  ("Slett valgte",self.delete_records),("Tøm skjema",self.clear_form)]
        for txt,cmd in btns:
            ttk.Button(action,text=txt,command=cmd).pack(side=tk.LEFT,padx=2)

    def on_table_select(self,event=None):
        self.build_data_entry(); self.populate_results_tree()
        self.status_var.set(f"Viser data for '{self.table_var.get()}'.")
    def populate_results_tree(self):
        tbl=self.table_var.get(); info=self.tables.get(tbl); 
        if not info: return
        for i in self.results_tree.get_children(): self.results_tree.delete(i)
        all_f=info['fields']
        if tbl=='brukere' and self.user_role!='admin':
            fields=[f for f in all_f if f!='passord']; pi=all_f.index('passord')
        else:
            fields=all_f[:]; pi=None
        self.results_tree['columns']=tuple(fields)
        self.results_tree.heading('#0',text=''); self.results_tree.column('#0',width=0,stretch=tk.NO)
        for c in fields:
            self.results_tree.heading(c,text=c)
            self.results_tree.column(c,anchor='center',width=120 if not self.is_mobile else 100)
        rows=db_manager.execute_query(info['select_query']) or []
        if self.user_role=='elev' and 'epost' in all_f:
            idx=all_f.index('epost'); rows=[r for r in rows if r[idx]==self.current_user]
        for r in rows:
            rr=tuple(v for i,v in enumerate(r) if i!=pi) if pi is not None else r
            self.results_tree.insert('', 'end', values=rr)
        self.status_var.set(f"{len(rows)} poster funnet i '{tbl}'.")
        self.reselect_first_row()

    def on_result_select(self,event=None):
        sels=self.results_tree.selection()
        self.details_text.configure(state='normal'); self.details_text.delete('1.0',tk.END)
        if not sels:
            self.details_text.insert(tk.END,"Ingen rad er valgt.")
        else:
            vals=self.results_tree.item(sels[0])['values']
            tbl=self.table_var.get(); info=self.tables.get(tbl,{}); all_f=info.get('fields',[])
            disp=[f for f in all_f if not (tbl=='brukere' and f=='passord' and self.user_role!='admin')]
            for f,v in zip(disp,vals):
                self.details_text.insert(tk.END,f"{f}: {v}\n")
        self.details_text.configure(state='disabled')

    def reselect_first_row(self):
        ch=self.results_tree.get_children()
        if ch: self.results_tree.selection_set(ch[0])
        else:
            self.details_text.configure(state='normal'); self.details_text.delete('1.0',tk.END)
            self.details_text.insert(tk.END,"Ingen rad er valgt."); self.details_text.configure(state='disabled')
        self.on_result_select()

    def perform_search(self,event=None):
        tbl=self.table_var.get(); info=self.tables.get(tbl,{})
        if not tbl: return
        term=self.search_entry.get().lower().strip()
        rows=db_manager.execute_query(info['select_query']) or []
        if self.user_role=='elev' and 'epost' in info.get('fields',[]):
            idx=info['fields'].index('epost'); rows=[r for r in rows if r[idx]==self.current_user]
        matches=[r for r in rows if any(term in str(v).lower() for v in r)]
        for i in self.results_tree.get_children(): self.results_tree.delete(i)
        pi=info['fields'].index('passord') if tbl=='brukere' and self.user_role!='admin' else None
        for r in matches:
            rr=tuple(v for i,v in enumerate(r) if i!=pi) if pi is not None else r
            self.results_tree.insert('', 'end', values=rr)
        self.status_var.set(f"Søket fant {len(matches)} poster."); self.reselect_first_row()

    def sort_results(self):
        tbl=self.table_var.get(); col=self.sort_var.get()
        if not tbl or not col:
            messagebox.showinfo("Sorter","Velg kolonne."); return
        info=self.tables.get(tbl,{})
        q=info['select_query']+f" ORDER BY {col} ASC"
        rows=db_manager.execute_query(q) or []
        if self.user_role=='elev' and 'epost' in info.get('fields',[]):
            idx=info['fields'].index('epost'); rows=[r for r in rows if r[idx]==self.current_user]
        for i in self.results_tree.get_children(): self.results_tree.delete(i)
        pi=info['fields'].index('passord') if tbl=='brukere' and self.user_role!='admin' else None
        for r in rows:
            rr=tuple(v for i,v in enumerate(r) if i!=pi) if pi is not None else r
            self.results_tree.insert('', 'end', values=rr)
        self.status_var.set(f"{len(rows)} poster sortert etter {col}."); self.reselect_first_row()

    def add_record(self):
        tbl=self.table_var.get()
        if not tbl: messagebox.showwarning("Advarsel","Velg en tabell først."); return
        vals=[w.get().strip() for w in self.entry_widgets.values()]
        if any(v=='' for v in vals):
            messagebox.showwarning("Advarsel","Alle felt må fylles ut."); return
        info=self.tables.get(tbl,{})
        if db_manager.execute_query(info['insert_query'],tuple(vals),commit=True) is None: return
        if tbl=='brukere':
            ep=self.entry_widgets['epost'].get().strip()
            secret=pyotp.random_base32()
            db_manager.execute_query("UPDATE brukere SET mfa_secret=%s WHERE epost=%s",(secret,ep),commit=True)
            uri=pyotp.TOTP(secret).provisioning_uri(name=ep,issuer_name="Skoleapplikasjon")
            qr_img=qrcode.make(uri)
            win=tk.Toplevel(self.root); win.title("Konfigurer 2FA"); win.geometry("300x350")
            ttk.Label(win,text="Skann denne QR-koden\nmed Microsoft Authenticator:",
                      font=("Arial",12),justify="center").pack(pady=10)
            tk_img=ImageTk.PhotoImage(qr_img); lbl=tk.Label(win,image=tk_img); lbl.image=tk_img; lbl.pack(pady=10)
            ttk.Button(win,text="Ferdig",command=win.destroy).pack(pady=(0,10))
        messagebox.showinfo("Suksess","Posten ble lagt til.")
        self.build_data_entry(); self.populate_results_tree()

    def populate_form_for_selected(self):
        sels=self.results_tree.selection()
        if not sels: messagebox.showwarning("Advarsel","Velg rad først."); return
        self.selected_item=sels[0]; tbl=self.table_var.get(); info=self.tables.get(tbl,{})
        all_f=info.get('fields',[]); vals=self.results_tree.item(self.selected_item)['values']
        full=db_manager.execute_query(info['select_query']+" WHERE "+ " AND ".join(f"{f}=%s" for f in all_f),tuple(vals)) or [[]]
        row=full[0] if full else []
        for i,f in enumerate(all_f):
            if f in self.entry_widgets:
                w=self.entry_widgets[f]; w.delete(0,tk.END); w.insert(0,str(row[i]))
        self.on_result_select()

    def update_selected_record(self):
        if not hasattr(self,'selected_item'):
            messagebox.showwarning("Advarsel","Velg og rediger rad først."); return
        tbl=self.table_var.get(); info=self.tables.get(tbl,{}); fields=info.get('fields',[])[:]
        new=[self.entry_widgets[f].get().strip() for f in fields if f in self.entry_widgets]
        if any(v=='' for v in new):
            messagebox.showwarning("Advarsel","Alle felt må fylles ut."); return
        old=list(self.results_tree.item(self.selected_item)['values'])
        if tbl=='brukere' and self.user_role!='admin':
            pi=fields.index('passord'); del fields[pi]; del old[pi]
        q=f"UPDATE {tbl} SET "+",".join(f"{f}=%s" for f in fields)+" WHERE "+ " AND ".join(f"{f}=%s" for f in fields)
        params=tuple(new+old)
        if db_manager.execute_query(q,params,commit=True) is None: return
        messagebox.showinfo("Suksess","Post oppdatert."); self.populate_results_tree()

    def update_all_records(self):
        tbl=self.table_var.get(); info=self.tables.get(tbl,{}); fields=info.get('fields',[])
        vals=[self.entry_widgets[f].get().strip() for f in fields if f in self.entry_widgets]
        if any(v=='' for v in vals):
            messagebox.showwarning("Advarsel","Alle felt må fylles ut."); return
        if not messagebox.askyesno("Bekreft","Oppdater alle poster?"): return
        q=f"UPDATE {tbl} SET "+",".join(f"{f}=%s" for f in fields if f in self.entry_widgets)
        if db_manager.execute_query(q,tuple(vals),commit=True) is None: return
        messagebox.showinfo("Suksess","Alle poster oppdatert."); self.populate_results_tree()

    def delete_records(self):
        tbl=self.table_var.get(); sels=self.results_tree.selection()
        if not tbl or not sels:
            messagebox.showwarning("Advarsel","Velg tabell og rader."); return
        if not messagebox.askyesno("Bekreft",f"Slette {len(sels)} poster?"): return
        cols=list(self.results_tree['columns'])
        for s in sels:
            vals=list(self.results_tree.item(s)['values'])
            q=f"DELETE FROM {tbl} WHERE "+ " AND ".join(f"{c}=%s" for c in cols)
            if db_manager.execute_query(q,tuple(vals),commit=True) is None: return
        messagebox.showinfo("Suksess",f"Slettet {len(sels)} poster."); self.populate_results_tree()

    def logout(self):
        self.root.destroy()
        root=tk.Tk(); LoginWindow(root); root.mainloop()

def main():
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
