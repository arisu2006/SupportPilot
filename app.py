"""
SupportPilot Milestone 1 — Flask app with login, SQLite, AI classification.
Any username + password "123" works.
Run:  python app.py
Open: http://127.0.0.1:5000
"""
from functools import wraps
from flask import (
    Flask, request, jsonify, render_template, redirect,
    url_for, flash, session
)
import database
import classifier

app = Flask(__name__)
app.secret_key = "supportpilot-dev-key"

database.init_db()

SEVERITY_MEANING = {
    "Critical": "Company-wide or safety-impacting outage. Fix immediately.",
    "High": "Blocks one person or team from working. Same-day fix.",
    "Medium": "Noticeable problem with a workaround. Fix within a few days.",
    "Low": "Minor inconvenience. Handle as routine backlog.",
}
PRIORITY_MEANING = {
    "P1": "Drop everything — assign a technician now.",
    "P2": "Same-day response expected.",
    "P3": "Schedule within the week.",
    "P4": "Routine queue, no urgency.",
}


@app.context_processor
def inject_meanings():
    return {
        "severity_meaning": SEVERITY_MEANING,
        "priority_meaning": PRIORITY_MEANING,
    }


def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapped


@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        # Any name allowed; password must be 123
        if username and password == "123":
            session["username"] = username
            session["full_name"] = username.title()
            session["role"] = "employee"
            return redirect(url_for("dashboard"))
        if not username:
            error = "Please enter a username"
        else:
            error = "Incorrect password. Use password: 123"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    tickets = database.get_all_tickets(limit=50)
    stats = database.get_stats()
    return render_template(
        "index.html",
        tickets=tickets,
        stats=stats,
        user=session,
        active="dashboard",
    )


@app.route("/submit", methods=["POST"])
@login_required
def submit_ticket():
    employee_name = request.form.get("employee_name", "").strip()
    email = request.form.get("email", "").strip()
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    department = request.form.get("department", "").strip()
    business_impact = request.form.get("business_impact", "Medium")

    if not description:
        flash("Please describe the issue before submitting.")
        return redirect(url_for("dashboard") + "#submit")

    category, confidence, severity, priority = classifier.process_ticket(
        description, business_impact
    )

    ticket_id = database.insert_ticket(
        employee_name=employee_name or session.get("full_name", ""),
        email=email,
        title=title or description[:40],
        description=description,
        department=department,
        category=category,
        severity=severity,
        priority=priority,
        confidence=confidence,
    )

    flash(
        f"Ticket #{ticket_id} submitted — Category: {category} ({confidence}%), "
        f"Severity: {severity}, Priority: {priority}"
    )
    return redirect(url_for("dashboard") + "#tickets")


@app.route("/api/ticket", methods=["POST"])
def api_create_ticket():
    data = request.get_json(silent=True) or {}
    description = data.get("description", "").strip()
    if not description:
        return jsonify({"error": "description is required"}), 400
    business_impact = data.get("business_impact", "Medium")
    category, confidence, severity, priority = classifier.process_ticket(
        description, business_impact
    )
    ticket_id = database.insert_ticket(
        employee_name=data.get("employee", data.get("employee_name", "")),
        email=data.get("email", ""),
        title=data.get("title", ""),
        description=description,
        department=data.get("department", ""),
        category=category,
        severity=severity,
        priority=priority,
        confidence=confidence,
    )
    return jsonify({
        "ticket_id": ticket_id,
        "ticket": description,
        "category": category,
        "confidence": confidence,
        "severity": severity,
        "priority": priority,
        "status": "Open",
    })


@app.route("/api/tickets", methods=["GET"])
def api_list_tickets():
    return jsonify(database.get_all_tickets(limit=100))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
