import tkinter as tk
from tkinter import messagebox

from core.auth import certify_user, remove_user, log_event
from core.db import get_db
from core.pki import init_ca

# ---------------- UI CONSTANTS ----------------
BG = "#0f172a"
PANEL = "#020617"
BTN = "#2563eb"
TXT = "white"


class AdminDashboard:
    def __init__(self, root, username):
        self.root = root
        self.username = username

        self.root.configure(bg=BG)

        self.container = tk.Frame(root, bg=BG)
        self.container.pack(fill="both", expand=True)

        self.build_header()
        self.build_controls()
        self.build_user_list()

    # ---------------- HEADER ----------------
    def build_header(self):
        header = tk.Frame(self.container, bg=PANEL, pady=15)
        header.pack(fill="x")

        tk.Label(
            header,
            text=f"Admin Dashboard — {self.username}",
            fg=TXT,
            bg=PANEL,
            font=("Segoe UI", 18, "bold")
        ).pack(side="left", padx=20)

        tk.Button(
            header,
            text="Logout",
            bg="#7f1d1d",
            fg=TXT,
            command=self.logout
        ).pack(side="right", padx=20)

    # ---------------- CONTROLS ----------------
    def build_controls(self):
        panel = tk.Frame(self.container, bg=BG, pady=20)
        panel.pack()

        tk.Button(
            panel,
            text="Init Root CA",
            bg=BTN,
            fg=TXT,
            width=25,
            command=self.init_ca_action
        ).pack(pady=10)

        tk.Label(panel, text="Target Username", fg=TXT, bg=BG).pack()
        self.user_entry = tk.Entry(panel, width=25)
        self.user_entry.pack(pady=5)

        tk.Button(
            panel,
            text="Certify User",
            bg=BTN,
            fg=TXT,
            width=25,
            command=self.certify
        ).pack(pady=5)

        tk.Button(
            panel,
            text="Delete User",
            bg="#991b1b",
            fg=TXT,
            width=25,
            command=self.delete_user
        ).pack(pady=5)

    # ---------------- USER LIST ----------------
    def build_user_list(self):
        panel = tk.Frame(self.container, bg=PANEL, padx=20, pady=20)
        panel.pack(pady=20)

        tk.Label(
            panel,
            text="Registered Users",
            fg=TXT,
            bg=PANEL,
            font=("Segoe UI", 14, "bold")
        ).pack()

        self.listbox = tk.Listbox(panel, width=60)
        self.listbox.pack(pady=10)

        self.refresh_users()

    def refresh_users(self):
        self.listbox.delete(0, tk.END)

        with get_db() as db:
            rows = db.execute(
                "SELECT username, role, department, certified FROM users"
            ).fetchall()

        for username, role, dept, cert in rows:
            status = "Certified" if cert else "Pending"
            self.listbox.insert(
                tk.END,
                f"{username} | {role} | {dept} | {status}"
            )

    # ---------------- ACTIONS ----------------
    def init_ca_action(self):
        try:
            init_ca()
            log_event(self.username, "INIT_CA")
            messagebox.showinfo("Success", "Root CA initialized successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def certify(self):
        user = self.user_entry.get().strip()

        if not user:
            messagebox.showwarning("Input Required", "Please enter a username.")
            return

        if user == "admin":
            messagebox.showwarning(
                "Not Allowed",
                "Admin does not require certification."
            )
            return

        try:
            certify_user(user)
            log_event(self.username, "CERTIFY_USER", user)
            messagebox.showinfo("Success", f"{user} certified successfully.")
            self.refresh_users()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_user(self):
        user = self.user_entry.get().strip()

        if not user:
            messagebox.showwarning("Input Required", "Please enter a username.")
            return

        if user == "admin":
            messagebox.showwarning(
                "Not Allowed",
                "Admin account cannot be deleted."
            )
            return

        if not messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{user}'?"
        ):
            return

        try:
            remove_user(user)
            log_event(self.username, "DELETE_USER", user)
            messagebox.showinfo("Deleted", f"{user} removed successfully.")
            self.refresh_users()
        except Exception as e:
            messagebox.showerror("Error", str(e))

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

