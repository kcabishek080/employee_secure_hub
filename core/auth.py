import hashlib
from core.db import get_db, init_tables
from core.db import get_db


# ---------------- PASSWORD UTILS ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ---------------- REGISTER USER ----------------
def register_user(username, password, role, department):
    with get_db() as db:
        db.execute(
            "INSERT INTO users (username, password, role, department) VALUES (?, ?, ?, ?)",
            (username, hash_password(password), role, department)
        )


# ---------------- LOGIN USER ----------------
def login_user(username, password):
    with get_db() as db:
        cur = db.execute(
            "SELECT username, role, department, certified "
            "FROM users WHERE username=? AND password=?",
            (username, hash_password(password))
        )
        user = cur.fetchone()   # ✅ FETCH INSIDE CONTEXT
    return user


# ---------------- CERTIFY USER ----------------
from core.db import get_db
from core.pki import issue_user_certificate

def certify_user(username):
    with get_db() as db:
        cur = db.execute(
            "UPDATE users SET certified = 1 WHERE username = ?",
            (username,)
        )
        if cur.rowcount == 0:
            raise Exception("User does not exist")

    # 🔑 THIS IS THE CRITICAL MISSING PART
    issue_user_certificate(username)



# ---------------- REMOVE USER ----------------
def remove_user(username):
    with get_db() as db:
        db.execute(
            "DELETE FROM users WHERE username=?",
            (username,)
        )


# ---------------- CHECK CERTIFIED ----------------
def is_certified(username):
    with get_db() as db:
        cur = db.execute(
            "SELECT certified FROM users WHERE username=?",
            (username,)
        )
        row = cur.fetchone()
    return bool(row and row[0] == 1)


# ---------------- AUDIT LOG ----------------
def log_event(actor, action, target=""):
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor TEXT,
                action TEXT,
                target TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute(
            "INSERT INTO audit_log (actor, action, target) VALUES (?, ?, ?)",
            (actor, action, target)
        )


# ---------------- DEFAULT ADMIN ----------------
def create_default_admin():
    # SAFETY: ensure tables exist even if app.py forgot
    init_tables()

    admin_user = "admin"
    admin_pass = hash_password("admin123")

    with get_db() as db:
        cur = db.execute(
            "SELECT username FROM users WHERE username=?",
            (admin_user,)
        )

        if not cur.fetchone():
            db.execute(
                "INSERT INTO users (username, password, role, department, certified) "
                "VALUES (?, ?, ?, ?, ?)",
                (admin_user, admin_pass, "Admin", "IT", 1)
            )

