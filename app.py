import tkinter as tk

from core.db import init_tables
from core.auth import create_default_admin
from login import LoginPage

if __name__ == "__main__":
    init_tables()
    create_default_admin()

    root = tk.Tk()
    root.title("Employee Secure Hub")
    root.geometry("1200x700")
    LoginPage(root)
    root.mainloop()
