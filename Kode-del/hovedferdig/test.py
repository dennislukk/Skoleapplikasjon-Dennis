import tkinter as tk
from tkinter import messagebox
import mysql.connector
from mysql.connector import Error

def test_connection():
    try:
        connection = mysql.connector.connect(
            host="10.10.25.55",
            user="dennis",
            password="r6dexMHMNE",  # <-- Sett inn riktig passord her
            database="HaarOgBlomster"
        )

        if connection.is_connected():
            messagebox.showinfo("Tilkobling", "Tilkobling til databasen fungerte!")
        else:
            messagebox.showwarning("Tilkobling", "Klarte ikke å koble til databasen.")
    except Error as e:
        messagebox.showerror("Feil", f"Noe gikk galt:\n{e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()

# Oppsett av GUI
root = tk.Tk()
root.title("MySQL Tilkoblingstester")

label = tk.Label(root, text="Test tilkobling til HaarOgBlomster-database", font=("Arial", 14))
label.pack(pady=10)

btn = tk.Button(root, text="Test tilkobling", command=test_connection, font=("Arial", 12))
btn.pack(pady=20)

root.geometry("400x150")
root.mainloop()
