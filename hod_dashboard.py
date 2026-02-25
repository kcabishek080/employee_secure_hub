import tkinter as tk
from tkinter import messagebox
from core.crypto_ops import list_inbox, verify_and_decrypt
import os

BG = "#0f172a"
PANEL = "#020617"
BTN = "#2563eb"
TXT = "white"


class HodDashboard:
    def __init__(self, root, username, department):
        self.root = root
        self.username = username
        self.department = department

        root.configure(bg=BG)
        self.container = tk.Frame(root, bg=BG)
        self.container.pack(fill="both", expand=True)

        self.build_header()
        self.build_inbox()

    # ---------------- HEADER ----------------
    def build_header(self):
        header = tk.Frame(self.container, bg=PANEL, pady=15)
        header.pack(fill="x")

        tk.Label(
            header,
            text=f"HOD Dashboard — {self.username} ({self.department})",
            fg=TXT, bg=PANEL,
            font=("Segoe UI", 18, "bold")
        ).pack(side="left", padx=20)

        tk.Button(
            header, text="Logout",
            bg="#7f1d1d", fg=TXT,
            command=self.logout
        ).pack(side="right", padx=20)

    # ---------------- INBOX ----------------
    def build_inbox(self):
        panel = tk.Frame(self.container, bg=PANEL, padx=30, pady=30)
        panel.pack(pady=30)

        tk.Label(
            panel, text="Encrypted Inbox",
            fg=TXT, bg=PANEL,
            font=("Segoe UI", 14, "bold")
        ).pack(pady=(0, 15))

        self.listbox = tk.Listbox(panel, width=60)
        self.listbox.pack(pady=10)

        self.refresh_inbox()

        tk.Button(
            panel,
            text="Verify Signature + Decrypt",
            bg=BTN, fg=TXT,
            width=30,
            command=self.open_package
        ).pack(pady=15)

    def refresh_inbox(self):
        self.listbox.delete(0, tk.END)
        for item in list_inbox(self.username):
            self.listbox.insert(tk.END, item)

    def open_package(self):
        if not self.listbox.curselection():
            messagebox.showwarning("Select File", "Select a package first.")
            return

        package = self.listbox.get(self.listbox.curselection())

        try:
            output = verify_and_decrypt(self.username, package)
            messagebox.showinfo(
                "Success",
                f"Signature verified.\nFile decrypted:\n{output}"
            )
        except Exception as e:
            messagebox.showerror(
                "Verification Failed",
                f"Integrity or trust validation failed:\n{e}"
            )

    def logout(self):
        # Close admin dashboard
        self.root.destroy()

        # Re-open Home / Login panel
        import tkinter as tk
        from login import LoginPage

        root = tk.Tk()
        root.title("Employee Secure Hub")
        root.geometry("1100x650")

        LoginPage(root)
        root.mainloop()
