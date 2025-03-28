import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector

class SchoolDatabaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("School Database Management")
        self.root.geometry("1400x800")

        # Database Configuration
        self.DB_CONFIG = {
            'host': "192.168.1.8",
            'user': "dennis",
            'password': "dennis",
            'database': "Skoleapplikasjon"
        }

        # Tables Dictionary (same as previous code)
        self.tables = {
             "rolle": {
        "fields": ["rolle_navn"],
        "insert_query": "INSERT INTO rolle (rolle_navn) VALUES (%s)",
        "select_query": "SELECT * FROM rolle"
    },
    "brukere": {
        "fields": ["fornavn", "etternavn", "rolle_navn", "epost"],
        "insert_query": "INSERT INTO brukere (fornavn, etternavn, rolle_navn, epost) VALUES (%s, %s, %s, %s)",
        "select_query": "SELECT * FROM brukere"
    },
    "admin": {
        "fields": ["epost"],
        "insert_query": "INSERT INTO admin (epost) VALUES (%s)",
        "select_query": "SELECT * FROM admin"
    },
    "laerer": {
        "fields": ["epost", "fag", "alder"],
        "insert_query": "INSERT INTO laerer (epost, fag, alder) VALUES (%s, %s, %s)",
        "select_query": "SELECT * FROM laerer"
    },
    "elever": {
        "fields": ["epost", "trinn", "fodselsdato"],
        "insert_query": "INSERT INTO elever (epost, trinn, fodselsdato) VALUES (%s, %s, %s)",
        "select_query": "SELECT * FROM elever"
    },
    "fag": {
        "fields": ["fag_navn"],
        "insert_query": "INSERT INTO fag (fag_navn) VALUES (%s)",
        "select_query": "SELECT * FROM fag"
    },
    "elev_fag": {
        "fields": ["epost", "fag_navn", "karakter"],
        "insert_query": "INSERT INTO elev_fag (epost, fag_navn, karakter) VALUES (%s, %s, %s)",
        "select_query": "SELECT * FROM elev_fag"
    },
    "oppgaver": {
        "fields": ["epost", "oppgave_tekst", "fag_navn"],
        "insert_query": "INSERT INTO oppgaver (epost, oppgave_tekst, fag_navn) VALUES (%s, %s, %s)",
        "select_query": "SELECT * FROM oppgaver"
    },
    "fravaer": {
        "fields": ["epost", "dato", "antall_timer"],
        "insert_query": "INSERT INTO fravaer (epost, dato, antall_timer) VALUES (%s, %s, %s)",
        "select_query": "SELECT * FROM fravaer"
    },
    "klasse": {
        "fields": ["klasse_navn"],
        "insert_query": "INSERT INTO klasse (klasse_navn) VALUES (%s)",
        "select_query": "SELECT * FROM klasse"
    },
    "klasse_elev": {
        "fields": ["klasse_navn", "epost"],
        "insert_query": "INSERT INTO klasse_elev (klasse_navn, epost) VALUES (%s, %s)",
        "select_query": "SELECT * FROM klasse_elev"
    },
    "klasse_laerer": {
        "fields": ["klasse_navn", "epost"],
        "insert_query": "INSERT INTO klasse_laerer (klasse_navn, epost) VALUES (%s, %s)",
        "select_query": "SELECT * FROM klasse_laerer"
    },
    "kontroll": {
        "fields": ["epost", "beskrivelse", "dato"],
        "insert_query": "INSERT INTO kontroll (epost, beskrivelse, dato) VALUES (%s, %s, %s)",
        "select_query": "SELECT * FROM kontroll"
    },
    "devices": {
        "fields": ["epost", "device_type", "device_model"],
        "insert_query": "INSERT INTO devices (epost, device_type, device_model) VALUES (%s, %s, %s)",
        "select_query": "SELECT * FROM devices"
    },
    "postdata": {
        "fields": ["epost", "innhold", "tidspunkt"],
        "insert_query": "INSERT INTO postdata (epost, innhold, tidspunkt) VALUES (%s, %s, %s)",
        "select_query": "SELECT * FROM postdata"
    },
    "start": {
        "fields": ["innstilling", "verdi"],
        "insert_query": "INSERT INTO start (innstilling, verdi) VALUES (%s, %s)",
        "select_query": "SELECT * FROM start"
    }

        }

        self.create_main_layout()

    def create_main_layout(self):
        # Main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top menu frame
        self.menu_frame = tk.Frame(self.main_frame)
        self.menu_frame.pack(fill=tk.X, pady=5)

        # Table selection dropdown
        self.table_var = tk.StringVar()
        self.table_dropdown = ttk.Combobox(self.menu_frame, 
                                            textvariable=self.table_var, 
                                            values=list(self.tables.keys()), 
                                            state="readonly", 
                                            width=30)
        self.table_dropdown.pack(side=tk.LEFT, padx=5)
        self.table_dropdown.bind("<<ComboboxSelected>>", self.on_table_select)

        # Search frame
        search_frame = tk.Frame(self.menu_frame)
        search_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, width=50)
        self.search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.search_entry.bind('<KeyRelease>', self.perform_search)

        # Main content area
        self.content_frame = tk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Left side - Data Entry
        self.data_entry_frame = tk.Frame(self.content_frame, width=400, relief=tk.RIDGE, borderwidth=1)
        self.data_entry_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10))
        self.data_entry_frame.pack_propagate(False)

        # Right side - Results
        self.results_frame = tk.Frame(self.content_frame)
        self.results_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Results Treeview with checkboxes
        self.results_tree = ttk.Treeview(self.results_frame, selectmode='extended', columns=('check',))
        self.results_tree.pack(fill=tk.BOTH, expand=True, anchor='w')
        
        # Configure the checkbox column
        self.results_tree.heading('check', text='Select')
        self.results_tree.column('check', width=50, anchor='center')
        
        # Bind selection event
        self.results_tree.bind('<<TreeviewSelect>>', self.on_result_select)
        
        # Checkbox click handler
        self.results_tree.bind('<Button-1>', self.toggle_checkbox)
        
        # Scrollbar for results
        scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscroll=scrollbar.set)

        # Action buttons
        action_frame = tk.Frame(self.results_frame)
        action_frame.pack(fill=tk.X, pady=5)

        tk.Button(action_frame, text="Add", command=self.add_record).pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Update Selected", command=self.update_selected_record).pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Update All", command=self.update_all_records).pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Delete", command=self.delete_records).pack(side=tk.LEFT, padx=5)

    def toggle_checkbox(self, event):
        # Get the column that was clicked
        region = self.results_tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.results_tree.identify_column(event.x)
            
            # Only toggle if the first column (checkbox) is clicked
            if column == '#1':
                # Get the row that was clicked
                row = self.results_tree.identify_row(event.y)
                
                # Toggle the checkbox
                current_values = self.results_tree.item(row, 'values')
                if len(current_values) > 0:
                    new_values = ('✓' if current_values[0] != '✓' else '', *current_values[1:])
                    self.results_tree.item(row, values=new_values)

    def on_table_select(self, event=None):
    # Clear previous data entry widgets
        for widget in self.data_entry_frame.winfo_children():
            widget.destroy()

        selected_table = self.table_var.get()
        if not selected_table:
            return

    # Create data entry widgets for the selected table
        self.entry_widgets = {}
        for i, field in enumerate(self.tables[selected_table]['fields']):
            frame = tk.Frame(self.data_entry_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
        
            label = tk.Label(frame, text=field, width=15, anchor='w')
            label.pack(side=tk.LEFT)

            # If the field is for "Navn" (combined from fornavn and etternavn), use a Combobox
            if field.endswith("_navn"):
                entry = ttk.Combobox(frame, width=30, state="readonly")
                # Fetch Navn (combined fornavn and etternavn) from brukere
                try:
                    conn = mysql.connector.connect(**self.DB_CONFIG)
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT {field} FROM {field.split('_')[0]}")
                    names = cursor.fetchall()
                    # Populate the combobox with the results from brukere
                    entry['values'] = [name[0] for name in names]
                except mysql.connector.Error as err:
                    messagebox.showerror("Database Error", str(err))
                finally:
                    conn.close()
            else:
                entry = tk.Entry(frame, width=30)

            entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
            self.entry_widgets[field] = entry

        # Populate results treeview
        self.populate_results_tree(selected_table)



    def populate_foreign_key_values(self, field, combobox):
        # Based on the field name, select the appropriate foreign key table
        table_name = field.split('_')[0]  # Extracts table name before '_navn'

        # Fetch foreign key values from the related table
        try:
            conn = mysql.connector.connect(**self.DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute(self.tables[table_name]['select_query'])
            
            values = [row[0] for row in cursor.fetchall()]
            combobox['values'] = values
        
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

    def populate_results_tree(self, table_name):
        # Clear existing treeview
        for i in self.results_tree.get_children():
            self.results_tree.delete(i)

        # Configure columns
        self.results_tree['columns'] = ('check',) + tuple(self.tables[table_name]['fields'])
        
        # Create column headings
        self.results_tree.heading('check', text='Select')
        self.results_tree.column('check', width=50, anchor='center')
        
        for field in self.tables[table_name]['fields']:
            self.results_tree.heading(field, text=field)
            self.results_tree.column(field, anchor='center', width=100)

        # Fetch and populate data
        try:
            conn = mysql.connector.connect(**self.DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute(self.tables[table_name]['select_query'])
            
            for row in cursor.fetchall():
                # Insert with an empty checkbox column
                self.results_tree.insert('', 'end', values=('',) + row)
        
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

    def on_result_select(self, event):
        # Get selected item
        selected_item = self.results_tree.selection()
        if not selected_item:
            return

        # Get the values of the selected item (skipping the checkbox column)
        values = self.results_tree.item(selected_item[0])['values'][1:]

        # Populate input fields with selected record
        for i, field in enumerate(self.tables[self.table_var.get()]['fields']):
            self.entry_widgets[field].delete(0, tk.END)
            self.entry_widgets[field].insert(0, values[i])

        # Store the selected item for later use in update
        self.selected_item = selected_item[0]

    def perform_search(self, event=None):
        # Get search term and selected table
        search_term = self.search_entry.get().lower()
        selected_table = self.table_var.get()
        
        if not selected_table:
            return

        # Clear existing items
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Fetch all data and filter
        try:
            conn = mysql.connector.connect(**self.DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute(self.tables[selected_table]['select_query'])
            
            for row in cursor.fetchall():
                # Convert row to string for case-insensitive search
                if any(search_term in str(val).lower() for val in row):
                    self.results_tree.insert('', 'end', values=('',) + row)
        
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

    def add_record(self):
        selected_table = self.table_var.get()
        if not selected_table:
            messagebox.showwarning("Warning", "Select a table first")
            return

        # Collect values from entry widgets
        values = [widget.get() for widget in self.entry_widgets.values()]

        # Validate input
        if any(val.strip() == '' for val in values):
            messagebox.showwarning("Warning", "All fields must be filled")
            return

        try:
            conn = mysql.connector.connect(**self.DB_CONFIG)
            cursor = conn.cursor()

            # Execute insert query
            cursor.execute(self.tables[selected_table]['insert_query'], tuple(values))

            conn.commit()
            messagebox.showinfo("Success", "Record added successfully")

            # Clear entry widgets
            for widget in self.entry_widgets.values():
                widget.delete(0, tk.END)

            # Refresh results
            self.populate_results_tree(selected_table)

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:    
            conn.close()

    def update_selected_record(self):
        selected_table = self.table_var.get()
        if not selected_table:
            messagebox.showwarning("Warning", "Select a table first")
            return

        # Check if a record is selected
        if not hasattr(self, 'selected_item'):
            messagebox.showwarning("Warning", "Select a record to update")
            return

        # Collect new values from entry widgets
        new_values = [widget.get() for widget in self.entry_widgets.values()]

        # Validate input
        if any(val.strip() == '' for val in new_values):
            messagebox.showwarning("Warning", "All fields must be filled")
            return

        try:
            conn = mysql.connector.connect(**self.DB_CONFIG)
            cursor = conn.cursor()

            # Prepare update query
            update_query = f"UPDATE {selected_table} SET "
            for i, field in enumerate(self.tables[selected_table]['fields']):
                update_query += f"{field} = %s"
                if i < len(self.tables[selected_table]['fields']) - 1:
                    update_query += ", "
            update_query += " WHERE "

            # Get the primary key of the selected record
            primary_key = self.results_tree.item(self.selected_item)['values'][1]

            update_query += f"{self.tables[selected_table]['fields'][0]} = %s"

            # Combine new values and primary key
            full_values = new_values + [primary_key]

            cursor.execute(update_query, tuple(full_values))

            conn.commit()
            messagebox.showinfo("Success", "Selected record updated successfully")

            # Refresh results
            self.populate_results_tree(selected_table)

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

    def update_all_records(self):
        selected_table = self.table_var.get()
        if not selected_table:
            messagebox.showwarning("Warning", "Select a table first")
            return

        # Collect values from entry widgets
        new_values = [widget.get() for widget in self.entry_widgets.values()]

        # Validate input
        if any(val.strip() == '' for val in new_values):
            messagebox.showwarning("Warning", "All fields must be filled")
            return

        # Confirm global update
        if not messagebox.askyesno("Confirm", "Are you sure you want to update ALL records with these values?"):
            return

        try:
            conn = mysql.connector.connect(**self.DB_CONFIG)
            cursor = conn.cursor()
            
            # Generic update query to set all rows to the same values
            update_query = f"""
            UPDATE {selected_table} 
            SET {', '.join(f'{field} = %s' for field in self.tables[selected_table]['fields'])}
            """
            
            cursor.execute(update_query, tuple(new_values))
            
            conn.commit()
            messagebox.showinfo("Success", f"All records in {selected_table} updated successfully")

            # Refresh results
            self.populate_results_tree(selected_table)

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

    def delete_records(self):
        selected_table = self.table_var.get()
        if not selected_table:
            messagebox.showwarning("Warning", "Select a table first")
            return

        # Get selected items with checkmark
        selected_items = [
            item for item in self.results_tree.get_children() 
            if self.results_tree.item(item)['values'][0] == '✓'
        ]

        if not selected_items:
            messagebox.showwarning("Warning", "Select records to delete")
            return

        # Confirm deletion
        if not messagebox.askyesno("Confirm", f"Are you sure you want to delete {len(selected_items)} records?"):
            return

        try:
            conn = mysql.connector.connect(**self.DB_CONFIG)
            cursor = conn.cursor()

            # Construct delete query dynamically
            delete_query = f"DELETE FROM {selected_table} WHERE {self.tables[selected_table]['fields'][0]} = %s"

            # Delete each selected record
            for item in selected_items:
                values = self.results_tree.item(item)['values'][1:]  # Skip checkbox column
                cursor.execute(delete_query, (values[0],))

            conn.commit()
            messagebox.showinfo("Success", f"{len(selected_items)} records deleted")

            # Refresh results
            self.populate_results_tree(selected_table)

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

def main():
    root = tk.Tk()
    app = SchoolDatabaseApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()