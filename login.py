import tkinter as tk
from tkinter import messagebox
from core.auth import register_user, login_user
from admin_dashboard import AdminDashboard
from employee_dashboard import EmployeeDashboard
from hod_dashboard import HodDashboard

BG = "#0f172a"
PANEL = "#020617"
BTN = "#2563eb"
TXT = "white"

class LoginPage:
    def __init__(self, root):
        self.root = root
        self.root.configure(bg=BG)

        self.container = tk.Frame(root, bg=BG)
        self.container.pack(fill="both", expand=True)

        tk.Label(
            self.container,
            text="Employee Secure Hub",
            font=("Segoe UI", 28, "bold"),
            fg=TXT,
            bg=BG
        ).pack(pady=25)

        self.login_panel()

    # ---------------- LOGIN PANEL ----------------
    def login_panel(self):
        self.clear_panel()

        panel = tk.Frame(self.container, bg=PANEL, padx=40, pady=40)
        panel.pack()

        tk.Label(panel, text="Login",
                 font=("Segoe UI", 20, "bold"),
                 fg=TXT, bg=PANEL).pack(pady=(0, 20))

        tk.Label(panel, text="Username", fg=TXT, bg=PANEL).pack(anchor="w")
        self.l_user = tk.Entry(panel, width=28)
        self.l_user.pack(pady=5)

        tk.Label(panel, text="Password", fg=TXT, bg=PANEL).pack(anchor="w")
        self.l_pass = tk.Entry(panel, show="*", width=28)
        self.l_pass.pack(pady=5)

        tk.Button(panel, text="Login",
                  bg=BTN, fg=TXT, width=22,
                  command=self.login).pack(pady=15)

        tk.Button(panel, text="Create Account",
                  bg="#334155", fg=TXT, width=22,
                  command=self.register_panel).pack()

    # ---------------- REGISTER PANEL ----------------
    def register_panel(self):
        self.clear_panel()

        panel = tk.Frame(self.container, bg=PANEL, padx=40, pady=40)
        panel.pack()

        tk.Label(panel, text="Create Account",
                 font=("Segoe UI", 20, "bold"),
                 fg=TXT, bg=PANEL).pack(pady=(0, 20))

        tk.Label(panel, text="Username", fg=TXT, bg=PANEL).pack(anchor="w")
        self.r_user = tk.Entry(panel, width=28)
        self.r_user.pack(pady=5)

        tk.Label(panel, text="Password", fg=TXT, bg=PANEL).pack(anchor="w")
        self.r_pass = tk.Entry(panel, show="*", width=28)
        self.r_pass.pack(pady=5)

        tk.Label(panel, text="Role", fg=TXT, bg=PANEL).pack(anchor="w")
        self.role = tk.StringVar(value="Employee")
        tk.OptionMenu(panel, self.role, "Employee", "HOD").pack(pady=5)

        tk.Label(panel, text="Department", fg=TXT, bg=PANEL).pack(anchor="w")
        self.dept = tk.Entry(panel, width=28)
        self.dept.pack(pady=5)

        tk.Button(panel, text="Register",
                  bg=BTN, fg=TXT, width=22,
                  command=self.register).pack(pady=15)

        tk.Button(panel, text="Back to Login",
                  bg="#334155", fg=TXT, width=22,
                  command=self.login_panel).pack()

    # ---------------- ACTIONS ----------------
    def login(self):
        user = login_user(self.l_user.get(), self.l_pass.get())
        if not user:
            messagebox.showerror("Login Failed", "Invalid username or password")
            return

        username, role, department, certified = user
        self.root.destroy()

        root = tk.Tk()
        root.title("Employee Secure Hub")
        root.geometry("1100x650")

        if role == "Admin":
            AdminDashboard(root, username)
        elif role == "HOD":
            HodDashboard(root, username, department)
        else:
            EmployeeDashboard(root, username, department, certified)

        root.mainloop()

    def register(self):
        try:
            register_user(
                self.r_user.get(),
                self.r_pass.get(),
                self.role.get(),
                self.dept.get()
            )
            messagebox.showinfo(
                "Registration Successful",
                "Account created successfully.\nPlease wait for admin certification."
            )
            self.login_panel()
        except:
            messagebox.showerror("Registration Failed", "Username already exists")

    def clear_panel(self):
        for widget in self.container.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.destroy()
