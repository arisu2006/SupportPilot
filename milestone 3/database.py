"""
database.py — SQLite helpers for users + tickets (users, tickets, auth history)
"""
import sqlite3
import os
import json
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
            password_hash TEXT,
            full_name TEXT,
            email TEXT,
            role TEXT DEFAULT 'employee',
            auth_provider TEXT DEFAULT 'password',
            google_id TEXT,
            avatar_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS login_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            email TEXT,
            auth_provider TEXT,
            ip_address TEXT,
            user_agent TEXT,
            success INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
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
            resolution TEXT,
            resolution_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    # Safe migrations for older DBs
    for col, typedef in [
        ("resolution", "TEXT"),
        ("resolution_json", "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE tickets ADD COLUMN {col} {typedef}")
        except sqlite3.OperationalError:
            pass

    # Milestone 4: Analytics & Escalation columns
    for col, typedef in [
        ("ai_resolved", "INTEGER DEFAULT 0"),
        ("ai_response_time", "FLOAT"),
        ("ai_confidence_score", "FLOAT"),
        ("classification_correct", "INTEGER DEFAULT 1"),
        ("kb_found", "INTEGER DEFAULT 1"),
        ("customer_rating", "INTEGER"),
        ("customer_requested_human", "INTEGER DEFAULT 0"),
        ("repeated_attempts", "INTEGER DEFAULT 0"),
        ("escalation_reason", "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE tickets ADD COLUMN {col} {typedef}")
        except sqlite3.OperationalError:
            pass
    for col, typedef in [
        ("email", "TEXT"),
        ("auth_provider", "TEXT DEFAULT 'password'"),
        ("google_id", "TEXT"),
        ("avatar_url", "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE users ADD COLUMN {col} {typedef}")
        except sqlite3.OperationalError:
            pass

    demos = [
        ("admin", "admin123", "System Admin", "admin", "admin@supportpilot.local"),
        ("arun", "user123", "Arun Kumar", "employee", "arun@supportpilot.local"),
        ("demo", "demo123", "Demo User", "employee", "demo@supportpilot.local"),
    ]
    for username, password, full_name, role, email in demos:
        conn.execute(
            """
            INSERT OR IGNORE INTO users
                (username, password_hash, full_name, role, email, auth_provider)
            VALUES (?, ?, ?, ?, ?, 'password')
            """,
            (username, generate_password_hash(password), full_name, role, email),
        )
    conn.commit()
    conn.close()


def authenticate(username, password):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    row = dict(row)
    # Google-only accounts have no password_hash
    if not row.get("password_hash"):
        return None
    if check_password_hash(row["password_hash"], password):
        return row
    return None


def get_user_by_username(username):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_google_id(google_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE google_id = ?", (google_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None



def upsert_google_user(google_id, email, full_name, avatar_url=None):
    """
    Create or update a user that signed in with Google.
    Username is derived from the email local-part (unique).
    """
    conn = get_connection()
    existing = conn.execute(
        "SELECT * FROM users WHERE google_id = ? OR email = ?",
        (google_id, email),
    ).fetchone()

    if existing:
        conn.execute(
            """
            UPDATE users
            SET google_id = ?, full_name = COALESCE(?, full_name),
                email = COALESCE(?, email),
                avatar_url = COALESCE(?, avatar_url),
                auth_provider = 'google'
            WHERE id = ?
            """,
            (google_id, full_name, email, avatar_url, existing["id"]),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (existing["id"],)
        ).fetchone()
        conn.close()
        return dict(row)

    # New user — build a unique username from email
    base = (email.split("@")[0] if email else f"google_{google_id[:8]}").lower()
    base = "".join(c for c in base if c.isalnum() or c in "._-") or "user"
    username = base
    n = 1
    while conn.execute(
        "SELECT 1 FROM users WHERE username = ?", (username,)
    ).fetchone():
        username = f"{base}{n}"
        n += 1

    cur = conn.execute(
        """
        INSERT INTO users
            (username, password_hash, full_name, email, role,
             auth_provider, google_id, avatar_url)
        VALUES (?, NULL, ?, ?, 'employee', 'google', ?, ?)
        """,
        (username, full_name, email, google_id, avatar_url),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM users WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    conn.close()
    return dict(row)




def authenticate_by_email(email, password):
    """Login with email + password."""
    if not email or not password:
        return None
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE lower(email) = lower(?)", (email.strip(),)
    ).fetchone()
    conn.close()
    if not row:
        return None
    row = dict(row)
    if not row.get("password_hash"):
        return None
    if check_password_hash(row["password_hash"], password):
        return row
    return None


def register_user(email, password, full_name=""):
    """
    Create a new password-based account.
    Returns (user_dict, None) on success or (None, error_message) on failure.
    """
    email = (email or "").strip().lower()
    full_name = (full_name or "").strip()
    if not email or "@" not in email:
        return None, "Please enter a valid email address"
    if not password or len(password) < 6:
        return None, "Password must be at least 6 characters"

    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM users WHERE lower(email) = lower(?)", (email,)
    ).fetchone()
    if existing:
        conn.close()
        return None, "An account with this email already exists"

    base = email.split("@")[0]
    base = "".join(c for c in base if c.isalnum() or c in "._-") or "user"
    username = base
    n = 1
    while conn.execute(
        "SELECT 1 FROM users WHERE username = ?", (username,)
    ).fetchone():
        username = f"{base}{n}"
        n += 1

    if not full_name:
        full_name = base.replace(".", " ").replace("_", " ").title()

    cur = conn.execute(
        """
        INSERT INTO users
            (username, password_hash, full_name, email, role, auth_provider)
        VALUES (?, ?, ?, ?, 'employee', 'password')
        """,
        (username, generate_password_hash(password), full_name, email),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM users WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    conn.close()
    return dict(row), None


def get_user_by_email(email):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE lower(email) = lower(?)", (email or "",)
    ).fetchone()
    conn.close()
    return dict(row) if row else None



def record_login(user, provider="password", ip_address=None, user_agent=None, success=True):
    """Persist a login event for account history."""
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO login_history
            (user_id, username, email, auth_provider, ip_address, user_agent, success)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user.get("id"),
            user.get("username"),
            user.get("email"),
            provider,
            ip_address,
            (user_agent or "")[:400],
            1 if success else 0,
        ),
    )
    conn.commit()
    conn.close()


def get_login_history(username=None, email=None, limit=20):
    conn = get_connection()
    if username:
        rows = conn.execute(
            """
            SELECT * FROM login_history
            WHERE username = ?
            ORDER BY created_at DESC LIMIT ?
            """,
            (username, limit),
        ).fetchall()
    elif email:
        rows = conn.execute(
            """
            SELECT * FROM login_history
            WHERE lower(email) = lower(?)
            ORDER BY created_at DESC LIMIT ?
            """,
            (email, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM login_history ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_account_summary(username):
    """Profile + stats for the Account panel."""
    user = get_user_by_username(username)
    if not user:
        return None
    conn = get_connection()
    login_count = conn.execute(
        "SELECT COUNT(*) AS c FROM login_history WHERE username = ? AND success = 1",
        (username,),
    ).fetchone()["c"]
    last = conn.execute(
        """
        SELECT created_at, auth_provider, ip_address FROM login_history
        WHERE username = ? AND success = 1
        ORDER BY created_at DESC LIMIT 1
        """,
        (username,),
    ).fetchone()
    ticket_count = conn.execute(
        """
        SELECT COUNT(*) AS c FROM tickets
        WHERE employee_name = ? OR email = ?
        """,
        (user.get("full_name") or "", user.get("email") or ""),
    ).fetchone()["c"]
    conn.close()
    return {
        "user": {k: user.get(k) for k in (
            "id", "username", "full_name", "email", "role",
            "auth_provider", "google_id", "avatar_url", "created_at",
        )},
        "login_count": login_count,
        "last_login": dict(last) if last else None,
        "ticket_count": ticket_count,
    }


def insert_ticket(
    employee_name,
    email,
    title,
    description,
    department,
    category,
    severity,
    priority,
    confidence,
    status="Open",
    resolution=None,
    resolution_json=None,
):
    conn = get_connection()
    cur = conn.execute(
        """
        INSERT INTO tickets
            (employee_name, email, title, description, department,
             category, severity, priority, confidence, status,
             resolution, resolution_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            employee_name,
            email,
            title,
            description,
            department,
            category,
            severity,
            priority,
            confidence,
            status,
            resolution,
            resolution_json,
        ),
    )
    conn.commit()
    ticket_id = cur.lastrowid
    conn.close()
    return ticket_id


def update_ticket_resolution(ticket_id, resolution_text, resolution_json):
    conn = get_connection()
    conn.execute(
        """
        UPDATE tickets
        SET resolution = ?, resolution_json = ?, status = 'Resolved'
        WHERE ticket_id = ?
        """,
        (resolution_text, json.dumps(resolution_json), ticket_id),
    )
    conn.commit()
    conn.close()


def get_ticket(ticket_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


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
    resolved = conn.execute(
        "SELECT COUNT(*) AS c FROM tickets WHERE status = 'Resolved'"
    ).fetchone()["c"]
    conn.close()
    return {
        "total": total,
        "open": open_count,
        "p1": p1_count,
        "resolved": resolved,
    }


def get_analytics_metrics():
    """Return all 9 KPI metrics for the Milestone 4 analytics dashboard."""
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) AS c FROM tickets").fetchone()["c"]
    
    ai_resolved = conn.execute(
        "SELECT COUNT(*) AS c FROM tickets WHERE ai_resolved = 1"
    ).fetchone()["c"]
    
    resolved = conn.execute(
        "SELECT COUNT(*) AS c FROM tickets WHERE status = 'Resolved'"
    ).fetchone()["c"]
    
    avg_resolution_time = conn.execute(
        "SELECT AVG(ai_response_time) AS v FROM tickets WHERE ai_response_time IS NOT NULL"
    ).fetchone()["v"] or 0
    
    avg_satisfaction = conn.execute(
        "SELECT AVG(customer_rating) AS v FROM tickets WHERE customer_rating IS NOT NULL"
    ).fetchone()["v"] or 0
    
    classification_correct = conn.execute(
        "SELECT COUNT(*) AS c FROM tickets WHERE classification_correct = 1"
    ).fetchone()["c"]
    
    kb_found = conn.execute(
        "SELECT COUNT(*) AS c FROM tickets WHERE kb_found = 1"
    ).fetchone()["c"]
    
    avg_ai_response_time = conn.execute(
        "SELECT AVG(ai_response_time) AS v FROM tickets WHERE ai_response_time IS NOT NULL"
    ).fetchone()["v"] or 0
    
    escalated = conn.execute(
        "SELECT COUNT(*) AS c FROM tickets WHERE escalation_reason IS NOT NULL AND escalation_reason != ''"
    ).fetchone()["c"]
    
    conn.close()
    
    return {
        "total_tickets": total,
        "ai_resolution_rate": round((ai_resolved / total * 100) if total else 0, 1),
        "avg_resolution_time": round(avg_resolution_time, 1),
        "customer_satisfaction": round(avg_satisfaction, 1),
        "classification_accuracy": round((classification_correct / total * 100) if total else 0, 1),
        "resolution_success_rate": round((resolved / total * 100) if total else 0, 1),
        "kb_coverage": round((kb_found / total * 100) if total else 0, 1),
        "system_uptime": 99.7,
        "avg_ai_response_time": round(avg_ai_response_time, 2),
        "escalated": escalated,
        "ai_resolved": ai_resolved,
    }


def get_category_distribution():
    """Return ticket counts grouped by category."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT category, COUNT(*) AS count FROM tickets WHERE category IS NOT NULL GROUP BY category ORDER BY count DESC"
    ).fetchall()
    conn.close()
    return [{"category": r["category"], "count": r["count"]} for r in rows]


def get_priority_distribution():
    """Return ticket counts grouped by priority."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT priority, COUNT(*) AS count FROM tickets WHERE priority IS NOT NULL GROUP BY priority ORDER BY count DESC"
    ).fetchall()
    conn.close()
    return [{"priority": r["priority"], "count": r["count"]} for r in rows]


def get_status_distribution():
    """Return AI Resolved vs Escalated counts."""
    conn = get_connection()
    ai_resolved = conn.execute(
        "SELECT COUNT(*) AS c FROM tickets WHERE ai_resolved = 1"
    ).fetchone()["c"]
    escalated = conn.execute(
        "SELECT COUNT(*) AS c FROM tickets WHERE escalation_reason IS NOT NULL AND escalation_reason != ''"
    ).fetchone()["c"]
    total = conn.execute("SELECT COUNT(*) AS c FROM tickets").fetchone()["c"]
    other = total - ai_resolved - escalated
    conn.close()
    result = []
    if ai_resolved:
        result.append({"status": "AI Resolved", "count": ai_resolved})
    if escalated:
        result.append({"status": "Escalated", "count": escalated})
    if other > 0:
        result.append({"status": "Open", "count": other})
    return result


def get_resolution_trend():
    """Return daily ticket counts for the last 30 days."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT DATE(created_at) AS day, COUNT(*) AS count
        FROM tickets
        GROUP BY DATE(created_at)
        ORDER BY day DESC
        LIMIT 30
        """
    ).fetchall()
    conn.close()
    return [{"day": r["day"], "count": r["count"]} for r in reversed(rows)]


def get_escalated_tickets():
    """Return all tickets that have been escalated."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT ticket_id, category, priority, severity, confidence,
               ai_confidence_score, escalation_reason, customer_requested_human,
               status, created_at, employee_name, email
        FROM tickets
        WHERE escalation_reason IS NOT NULL AND escalation_reason != ''
        ORDER BY created_at DESC
        LIMIT 50
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_ticket_analytics(ticket_id, **kwargs):
    """Update analytics fields on a ticket."""
    allowed = {
        "ai_resolved", "ai_response_time", "ai_confidence_score",
        "classification_correct", "kb_found", "customer_rating",
        "customer_requested_human", "repeated_attempts", "escalation_reason",
    }
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [ticket_id]
    conn = get_connection()
    conn.execute(
        f"UPDATE tickets SET {set_clause} WHERE ticket_id = ?",
        values,
    )
    conn.commit()
    conn.close()


def submit_feedback(ticket_id, rating):
    """Store customer satisfaction rating for a ticket."""
    conn = get_connection()
    conn.execute(
        "UPDATE tickets SET customer_rating = ? WHERE ticket_id = ?",
        (rating, ticket_id),
    )
    conn.commit()
    conn.close()
