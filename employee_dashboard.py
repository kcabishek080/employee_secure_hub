import tkinter as tk
from tkinter import messagebox, filedialog
from core.pki import has_valid_cert, nonce_authenticate
from core.crypto_ops import encrypt_and_sign_file
import os

BG = "#0f172a"
PANEL = "#020617"
BTN = "#2563eb"
TXT = "white"


class EmployeeDashboard:
    def __init__(self, root, username, department, certified):
        self.root = root
        self.username = username
        self.department = department
        self.certified = certified

        root.configure(bg=BG)
        self.container = tk.Frame(root, bg=BG)
        self.container.pack(fill="both", expand=True)

        self.build_header()
        self.build_status_panel()
        self.build_file_panel()

    # ---------------- HEADER ----------------
    def build_header(self):
        header = tk.Frame(self.container, bg=PANEL, pady=15)
        header.pack(fill="x")

        tk.Label(
            header,
            text=f"Employee Dashboard — {self.username}",
            fg=TXT, bg=PANEL,
            font=("Segoe UI", 18, "bold")
        ).pack(side="left", padx=20)

        tk.Button(
            header, text="Logout",
            bg="#7f1d1d", fg=TXT,
            command=self.logout
        ).pack(side="right", padx=20)

    # ---------------- STATUS PANEL ----------------
    def build_status_panel(self):
        panel = tk.Frame(self.container, bg=BG, pady=30)
        panel.pack()

        cert_state = "VALID" if has_valid_cert(self.username) else "NOT ISSUED"

        self.cert_label = tk.Label(
            panel,
            text=f"Certificate Status: {cert_state}",
            fg="lightgreen" if cert_state == "VALID" else "orange",
            bg=BG,
            font=("Segoe UI", 12, "bold")
        )
        self.cert_label.pack(pady=10)

        tk.Button(
            panel,
            text="Nonce Authenticate",
            width=25,
            bg=BTN, fg=TXT,
            command=self.nonce_auth
        ).pack(pady=10)

        self.nonce_result = tk.Label(panel, text="", bg=BG)
        self.nonce_result.pack()

    # ---------------- FILE SHARING ----------------
    def build_file_panel(self):
        panel = tk.Frame(self.container, bg=PANEL, padx=30, pady=30)
        panel.pack(pady=20)

        tk.Label(
            panel, text="Send Encrypted Document",
            fg=TXT, bg=PANEL,
            font=("Segoe UI", 14, "bold")
        ).pack(pady=(0, 15))

        tk.Label(panel, text="Recipient (HOD username)", fg=TXT, bg=PANEL).pack(anchor="w")
        self.recipient_entry = tk.Entry(panel, width=35)
        self.recipient_entry.pack(pady=5)

        tk.Button(
            panel,
            text="Choose File + Encrypt + Sign + Send",
            bg=BTN, fg=TXT,
            width=30,
            command=self.send_file
        ).pack(pady=15)

    # ---------------- ACTIONS ----------------
    def nonce_auth(self):
        try:
            nonce_authenticate(self.username)
            self.nonce_result.config(
                text="✔ Nonce Authentication Successful",
                fg="lightgreen"
            )
        except Exception as e:
            self.nonce_result.config(
                text=f"✖ Nonce Authentication Failed: {e}",
                fg="red"
            )

    def send_file(self):
        if not has_valid_cert(self.username):
            messagebox.showerror("Error", "You must have a valid certificate.")
            return

        recipient = self.recipient_entry.get().strip()
        if not recipient:
            messagebox.showwarning("Input Required", "Enter recipient username.")
            return

        file_path = filedialog.askopenfilename()
        if not file_path:
            return

        try:
            encrypt_and_sign_file(
                sender=self.username,
                recipient=recipient,
                file_path=file_path
            )
            messagebox.showinfo(
                "Success",
                "File encrypted, signed, and sent successfully."
            )
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
