"""
database.py — SQLite helpers for users + tickets
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tickets.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'employee',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name VARCHAR(100),
            email VARCHAR(150),
            title VARCHAR(255),
            description TEXT,
            department VARCHAR(100),
            category VARCHAR(50),
            severity VARCHAR(20),
            priority VARCHAR(10),
            confidence FLOAT,
            status VARCHAR(30) DEFAULT 'Open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    # Demo users (password hashed)
    demos = [
        ("admin", "admin123", "System Admin", "admin"),
        ("arun", "user123", "Arun Kumar", "employee"),
        ("demo", "demo123", "Demo User", "employee"),
    ]
    for username, password, full_name, role in demos:
        conn.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, full_name, role) VALUES (?,?,?,?)",
            (username, generate_password_hash(password), full_name, role),
        )
    conn.commit()
    conn.close()


def authenticate(username, password):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if row and check_password_hash(row["password_hash"], password):
        return dict(row)
    return None


def insert_ticket(employee_name, email, title, description, department,
                  category, severity, priority, confidence, status="Open"):
    conn = get_connection()
    cur = conn.execute(
        """
        INSERT INTO tickets
            (employee_name, email, title, description, department,
             category, severity, priority, confidence, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (employee_name, email, title, description, department,
         category, severity, priority, confidence, status),
    )
    conn.commit()
    ticket_id = cur.lastrowid
    conn.close()
    return ticket_id


def get_all_tickets(limit=50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM tickets ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_stats():
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) AS c FROM tickets").fetchone()["c"]
    open_count = conn.execute(
        "SELECT COUNT(*) AS c FROM tickets WHERE status = 'Open'"
    ).fetchone()["c"]
    p1_count = conn.execute(
        "SELECT COUNT(*) AS c FROM tickets WHERE priority = 'P1'"
    ).fetchone()["c"]
    conn.close()
    return {"total": total, "open": open_count, "p1": p1_count}
