"""
SupportPilot — AI Ticket Resolution Agent
Login → JWT → Dashboard → Resolution
Milestone 3: Multi-Agent Workflows & Integrations (Jira + Email)
"""
from functools import wraps
import json
import os
from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
    flash,
    session,
    make_response,
)
from dotenv import load_dotenv

load_dotenv(override=True)

import database
import classifier
from rag import run_rag_pipeline, get_rag_metrics
from auth import (
    create_access_token,
    decode_access_token,
    login_required,
    JWT_EXPIRE_HOURS,
)
from agents import SupportPilot
from jira_service import JiraService
from email_service import EmailService

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "supportpilot-secret-key")

database.init_db()

# Milestone 3 services
support_pilot = SupportPilot()
jira_service = JiraService()
email_service = EmailService()

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
def inject_globals():
    return {
        "severity_meaning": SEVERITY_MEANING,
        "priority_meaning": PRIORITY_MEANING,
    }


def _establish_session(user: dict, provider: str = "password"):
    """Set Flask session fields from a user row."""
    session["username"] = user["username"]
    session["full_name"] = user.get("full_name") or user["username"].title()
    session["role"] = user.get("role") or "employee"
    session["email"] = user.get("email") or ""
    session["auth_provider"] = provider
    session["avatar_url"] = user.get("avatar_url") or ""


def _client_meta():
    return {
        "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "ua": request.headers.get("User-Agent", ""),
    }


def _issue_token_response(user: dict, provider: str, redirect_to_dashboard=True):
    """Create JWT, set cookie, record login history, optionally redirect."""
    if not user or not user.get("username"):
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "login_failed"}), 500
        flash("Sign-in failed. Please try again.")
        return redirect(url_for("login"))

    try:
        token = create_access_token(
            username=user["username"],
            full_name=user.get("full_name") or user["username"],
            role=user.get("role") or "employee",
            email=user.get("email") or "",
            auth_provider=provider,
        )
        if isinstance(token, bytes):
            token = token.decode("utf-8")
    except Exception:
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "token_error"}), 500
        flash("Could not create session. Please try again.")
        return redirect(url_for("login"))

    _establish_session(user, provider)
    meta = _client_meta()
    try:
        database.record_login(user, provider=provider, ip_address=meta["ip"], user_agent=meta["ua"])
    except Exception:
        pass

    if request.is_json or request.path.startswith("/api/"):
        return jsonify(
            {
                "access_token": token,
                "token_type": "Bearer",
                "expires_in_hours": JWT_EXPIRE_HOURS,
                "user": {
                    "username": user["username"],
                    "full_name": user.get("full_name"),
                    "email": user.get("email"),
                    "role": user.get("role"),
                    "provider": provider,
                },
            }
        )

    resp = make_response(redirect(url_for("dashboard")))
    resp.set_cookie(
        "sp_token",
        str(token),
        httponly=True,
        samesite="Lax",
        max_age=JWT_EXPIRE_HOURS * 3600,
        path="/",
    )
    return resp


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
    mode = "signin"
    if request.method == "POST":
        try:
            email = (request.form.get("email") or "").strip()
            password = request.form.get("password") or ""

            user = None
            if email:
                user = database.authenticate_by_email(email, password)
                if not user:
                    # Username login (no @) or local-part fallback
                    local = email.split("@")[0] if "@" in email else email
                    user = database.authenticate(local, password)

            if user:
                return _issue_token_response(user, "password")

            if not email:
                error = "Please enter your email"
            elif not password:
                error = "Please enter your password"
            else:
                error = "Invalid email or password"
        except Exception:
            error = "Sign-in failed. Please try again."

    return render_template("login.html", error=error, mode=mode)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "username" in session:
        return redirect(url_for("dashboard"))
    error = None
    mode = "signup"
    if request.method == "POST":
        try:
            email = (request.form.get("email") or "").strip()
            password = request.form.get("password") or ""
            full_name = (request.form.get("full_name") or "").strip()
            confirm = request.form.get("confirm_password") or ""

            if not email or not password:
                error = "Email and password are required"
            elif len(password) < 6:
                error = "Password must be at least 6 characters"
            elif password != confirm:
                error = "Passwords do not match"
            else:
                user, err = database.register_user(email, password, full_name)
                if err:
                    error = err
                elif not user:
                    error = "Could not create account. Please try again."
                else:
                    flash("Account created successfully. Welcome aboard!")
                    return _issue_token_response(user, "password")
        except Exception:
            error = "Sign-up failed. Please try again."

    return render_template("login.html", error=error, mode=mode)


@app.route("/auth/google", methods=["GET", "POST"])
def auth_google():
    """
    One-click Google sign-in (demo).
    No account picker — instantly enters as a demo Google user.
    """
    if "username" in session:
        return redirect(url_for("dashboard"))

    google_id = "google-demo-supportpilot-001"
    email = "alex.rivera@gmail.com"
    full_name = "Alex Rivera"
    avatar_url = "https://ui-avatars.com/api/?name=Alex+Rivera&background=4F46E5&color=fff&size=128"

    try:
        user = database.upsert_google_user(
            google_id=google_id,
            email=email,
            full_name=full_name,
            avatar_url=avatar_url,
        )
    except Exception:
        user = None

    if not user:
        flash("Google sign-in failed. Please try email login.")
        return redirect(url_for("login"))

    return _issue_token_response(user, "google")


@app.route("/api/auth/google", methods=["POST"])
def api_auth_google():
    """JSON one-click Google login (same demo identity)."""
    google_id = "google-demo-supportpilot-001"
    email = "alex.rivera@gmail.com"
    full_name = "Alex Rivera"
    avatar_url = "https://ui-avatars.com/api/?name=Alex+Rivera&background=4F46E5&color=fff&size=128"
    user = database.upsert_google_user(
        google_id=google_id,
        email=email,
        full_name=full_name,
        avatar_url=avatar_url,
    )
    return _issue_token_response(user, "google")


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    """JSON email/password login → JWT."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or data.get("username") or "").strip()
    password = data.get("password") or ""

    user = database.authenticate_by_email(email, password) if email else None
    if not user and email and "@" not in email:
        user = database.authenticate(email, password)
    if not user:
        return jsonify({"error": "invalid_credentials"}), 401

    token = create_access_token(
        username=user["username"],
        full_name=user.get("full_name") or user["username"],
        role=user.get("role") or "employee",
        email=user.get("email") or email,
        auth_provider="password",
    )
    meta = _client_meta()
    try:
        database.record_login(user, provider="password", ip_address=meta["ip"], user_agent=meta["ua"])
    except Exception:
        pass
    return jsonify(
        {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in_hours": JWT_EXPIRE_HOURS,
            "user": {
                "username": user["username"],
                "full_name": user.get("full_name"),
                "email": user.get("email"),
                "role": user.get("role"),
                "provider": "password",
            },
        }
    )


@app.route("/api/auth/signup", methods=["POST"])
def api_signup():
    """JSON registration → JWT."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    full_name = (data.get("full_name") or data.get("name") or "").strip()
    user, err = database.register_user(email, password, full_name)
    if err:
        return jsonify({"error": err}), 400
    meta = _client_meta()
    try:
        database.record_login(user, provider="password", ip_address=meta["ip"], user_agent=meta["ua"])
    except Exception:
        pass
    token = create_access_token(
        username=user["username"],
        full_name=user.get("full_name") or user["username"],
        role=user.get("role") or "employee",
        email=user.get("email") or email,
        auth_provider="password",
    )
    return jsonify(
        {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in_hours": JWT_EXPIRE_HOURS,
            "user": {
                "username": user["username"],
                "full_name": user.get("full_name"),
                "email": user.get("email"),
                "role": user.get("role"),
                "provider": "password",
            },
        }
    ), 201



@app.route("/api/auth/me", methods=["GET"])
@login_required
def api_me():
    return jsonify(
        {
            "username": session.get("username"),
            "full_name": session.get("full_name"),
            "email": session.get("email"),
            "role": session.get("role"),
            "provider": session.get("auth_provider"),
            "avatar_url": session.get("avatar_url"),
        }
    )


# ── PPT-style JWT endpoints (register / login / profile) ──────────────
@app.route("/register", methods=["POST"])
@app.route("/api/register", methods=["POST"])
def register_ppt():
    """PPT Step 6: User Registration — JSON body."""
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    full_name = (data.get("full_name") or data.get("name") or "").strip()

    if not password:
        return jsonify({"error": "Username and password are required"}), 400
    if not email and username:
        email = f"{username}@supportpilot.local"
    if not email:
        return jsonify({"error": "Username and password are required"}), 400

    user, err = database.register_user(email, password, full_name or username)
    if err:
        code = 409 if "exists" in err.lower() else 400
        return jsonify({"error": err}), code
    return jsonify({"message": "User registered successfully", "username": user["username"]}), 201


@app.route("/api/login", methods=["POST"])
def login_ppt():
    """PPT Step 7: Login — returns JWT token."""
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or username or "").strip()
    password = data.get("password") or ""

    user = database.authenticate_by_email(email, password) if email else None
    if not user and username:
        user = database.authenticate(username, password)
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(
        username=user["username"],
        full_name=user.get("full_name") or user["username"],
        role=user.get("role") or "employee",
        email=user.get("email") or email,
        auth_provider="password",
    )
    meta = _client_meta()
    try:
        database.record_login(user, provider="password", ip_address=meta["ip"], user_agent=meta["ua"])
    except Exception:
        pass
    return jsonify({"token": token}), 200


@app.route("/profile", methods=["GET"])
@app.route("/api/profile", methods=["GET"])
@login_required
def profile_ppt():
    """PPT Step 8: Protected route — JWT required."""
    return jsonify({
        "logged_in_as": session.get("username"),
        "full_name": session.get("full_name"),
        "email": session.get("email"),
        "role": session.get("role"),
    }), 200


@app.route("/logout")
def logout():
    session.clear()
    resp = make_response(redirect(url_for("login")))
    resp.set_cookie("sp_token", "", expires=0)
    return resp


@app.route("/dashboard")
@login_required
def dashboard():
    tickets = database.get_all_tickets(limit=50)
    stats = database.get_stats()
    metrics = get_rag_metrics()
    username = session.get("username")
    account = database.get_account_summary(username) if username else None
    history = database.get_login_history(username=username, limit=15) if username else []
    return render_template(
        "index.html",
        tickets=tickets,
        stats=stats,
        metrics=metrics,
        user=session,
        account=account,
        login_history=history,
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
    run_rag = request.form.get("run_rag") == "on"

    if not description:
        flash("Please describe the issue before submitting.")
        return redirect(url_for("dashboard") + "#submit")

    category, confidence, severity, priority = classifier.process_ticket(
        description, business_impact
    )

    resolution_text = None
    resolution_json = None
    rag_result = None

    if run_rag:
        ticket_payload = {
            "id": "pending",
            "title": title or description[:60],
            "description": description,
            "category": category,
            "priority": priority,
        }
        rag_result = run_rag_pipeline(ticket_payload)
        resolution_text = rag_result["resolution"]["full_text"]
        resolution_json = rag_result

    ticket_id = database.insert_ticket(
        employee_name=employee_name or session.get("full_name", ""),
        email=email or session.get("email", ""),
        title=title or description[:40],
        description=description,
        department=department,
        category=category,
        severity=severity,
        priority=priority,
        confidence=confidence,
        status="Resolved" if (run_rag and resolution_text) else "Open",
        resolution=resolution_text,
        resolution_json=json.dumps(resolution_json) if resolution_json else None,
    )

    if run_rag and rag_result:
        flash(
            f"Ticket #{ticket_id} classified & resolved by AI — "
            f"{category} ({confidence}%) · {severity}/{priority} · "
            f"RAG latency {rag_result['latency_ms']} ms"
        )
        return redirect(url_for("dashboard") + f"#resolve&ticket={ticket_id}")

    flash(
        f"Ticket #{ticket_id} submitted — Category: {category} ({confidence}%), "
        f"Severity: {severity}, Priority: {priority}"
    )
    return redirect(url_for("dashboard") + "#tickets")


@app.route("/api/ticket", methods=["POST"])
@login_required
def api_create_ticket():
    """Create ticket, always persist to SQLite, then optionally run RAG."""
    data = request.get_json(silent=True) or {}
    description = data.get("description", "").strip()
    if not description:
        return jsonify({"error": "description is required"}), 400

    business_impact = data.get("business_impact", "Medium")
    run_rag = data.get("run_rag", True)
    title = (data.get("title") or "").strip() or description[:40]

    # Classification — fall back safely if model fails
    try:
        category, confidence, severity, priority = classifier.process_ticket(
            description, business_impact
        )
    except Exception:
        category, confidence, severity, priority = "General", 50.0, "Medium", "P3"

    resolution_text = None
    resolution_json = None
    rag_result = None

    if run_rag:
        try:
            ticket_payload = {
                "id": "pending",
                "title": title,
                "description": description,
                "category": category,
                "priority": priority,
            }
            rag_result = run_rag_pipeline(ticket_payload)
            resolution_text = rag_result["resolution"]["full_text"]
            resolution_json = rag_result
        except Exception as exc:
            # Ticket still gets stored even if RAG fails
            rag_result = {
                "status": "ERROR",
                "latency_ms": 0,
                "analysis": {"keywords": [], "query": description.lower()},
                "context": "",
                "resolution": {
                    "status": "ERROR",
                    "full_text": f"RAG pipeline error: {exc}",
                    "steps": [],
                },
                "retrieved_documents": [],
                "workflow": {
                    "ticket_analysis": "completed",
                    "knowledge_retrieval": "failed",
                    "context_augmentation": "failed",
                    "response_generation": "failed",
                },
            }

    # Always persist ticket to SQLite
    ticket_id = database.insert_ticket(
        employee_name=data.get("employee", data.get("employee_name", session.get("full_name", ""))),
        email=data.get("email", session.get("email", "")),
        title=title,
        description=description,
        department=data.get("department", ""),
        category=category,
        severity=severity,
        priority=priority,
        confidence=confidence,
        status="Resolved" if resolution_text else "Open",
        resolution=resolution_text,
        resolution_json=json.dumps(resolution_json) if resolution_json else None,
    )

    payload = {
        "ticket_id": ticket_id,
        "title": title,
        "description": description,
        "category": category,
        "confidence": confidence,
        "severity": severity,
        "priority": priority,
        "status": "Resolved" if resolution_text else "Open",
        "stored": True,
    }
    if rag_result:
        payload["rag"] = {
            "status": rag_result.get("status"),
            "latency_ms": rag_result.get("latency_ms"),
            "analysis": rag_result.get("analysis"),
            "context": rag_result.get("context"),
            "resolution": rag_result.get("resolution"),
            "retrieved_documents": rag_result.get("retrieved_documents") or [],
            "workflow": rag_result.get("workflow") or {},
            "classification": {
                "category": category,
                "confidence": confidence,
                "severity": severity,
                "priority": priority,
            },
        }
    return jsonify(payload)


@app.route("/api/tickets", methods=["GET"])
@login_required
def api_list_tickets():
    return jsonify(database.get_all_tickets(limit=100))


@app.route("/api/ticket/<int:ticket_id>", methods=["GET"])
@login_required
def api_get_ticket(ticket_id):
    t = database.get_ticket(ticket_id)
    if not t:
        return jsonify({"error": "not found"}), 404
    if t.get("resolution_json"):
        try:
            t["rag"] = json.loads(t["resolution_json"])
        except Exception:
            t["rag"] = None
    return jsonify(t)


@app.route("/api/rag", methods=["POST"])
@login_required
def api_rag():
    data = request.get_json(silent=True) or {}
    description = data.get("description", "").strip()
    title = data.get("title", "").strip() or description[:60]
    if not description:
        return jsonify({"error": "description is required"}), 400

    category, confidence, severity, priority = classifier.process_ticket(
        description, data.get("business_impact", "Medium")
    )
    ticket_payload = {
        "id": data.get("id", "adhoc"),
        "title": title,
        "description": description,
        "category": category,
        "priority": priority,
    }
    result = run_rag_pipeline(ticket_payload)
    result["classification"] = {
        "category": category,
        "confidence": confidence,
        "severity": severity,
        "priority": priority,
    }
    return jsonify(result)


@app.route("/api/rag/metrics", methods=["GET"])
@login_required
def api_rag_metrics():
    return jsonify(get_rag_metrics())


@app.route("/resolve/<int:ticket_id>")
@login_required
def resolve_ticket(ticket_id):
    t = database.get_ticket(ticket_id)
    if not t:
        flash("Ticket not found.")
        return redirect(url_for("dashboard") + "#tickets")

    ticket_payload = {
        "id": t["ticket_id"],
        "title": t.get("title") or "",
        "description": t.get("description") or "",
        "category": t.get("category"),
        "priority": t.get("priority"),
    }
    rag_result = run_rag_pipeline(ticket_payload)
    resolution_text = rag_result["resolution"]["full_text"]
    database.update_ticket_resolution(ticket_id, resolution_text, rag_result)
    flash(
        f"Ticket #{ticket_id} resolved via RAG in {rag_result['latency_ms']} ms"
    )
    return redirect(url_for("dashboard") + f"#resolve&ticket={ticket_id}")



@app.route("/api/account", methods=["GET"])
@login_required
def api_account():
    username = session.get("username")
    summary = database.get_account_summary(username)
    history = database.get_login_history(username=username, limit=25)
    return jsonify({"account": summary, "login_history": history})


@app.route("/api/account/history", methods=["GET"])
@login_required
def api_account_history():
    username = session.get("username")
    return jsonify(database.get_login_history(username=username, limit=50))


# =========================================================
# MILESTONE 3 — Multi-Agent Workflows & Integrations
# =========================================================

@app.route("/multi-agent")
@login_required
def multi_agent_page():
    return render_template("multi_agent.html")


@app.route("/api/multi-agent", methods=["POST"])
@login_required
def api_multi_agent():
    """
    Process a ticket through the multi-agent pipeline:
    Diagnosis → Retrieval → Resolution → Validation → Escalate/Auto-resolve.
    On AUTO_RESOLVE: optionally send email.
    On ESCALATE: create Jira ticket.
    """
    data = request.get_json(silent=True) or {}
    ticket = (data.get("ticket") or data.get("description") or "").strip()
    user_email = (data.get("email") or session.get("email") or "").strip()

    if not ticket:
        return jsonify({"success": False, "message": "Ticket description required"}), 400

    result = support_pilot.process_ticket(ticket)
    confidence = result["validation"]["confidence"]
    status = result["validation"]["status"]

    response_payload = {
        "success": True,
        "status": status,
        "confidence": confidence,
        "result": result,
        "email": None,
        "jira": None,
    }

    if status == "AUTO_RESOLVE":
        if user_email:
            steps_text = "\n".join(
                f"{i + 1}. {step}" for i, step in enumerate(result["resolution"]["steps"])
            )
            email_body = (
                f"{result['resolution']['response']}\n\n"
                f"{steps_text}\n\n"
                f"Resolution confidence: {confidence}%\n\n"
                "Regards,\nSupportPilot AI Desk"
            )
            response_payload["email"] = email_service.send_email(
                user_email,
                "[SupportPilot] Ticket Auto-Resolved",
                email_body,
            )
        else:
            response_payload["email"] = {
                "success": False,
                "message": "No email provided; skipped notification",
            }
    else:
        # ESCALATE → Jira + Email Notification
        jira_result = jira_service.create_ticket(
            summary=result["diagnosis"]["diagnosis"],
            description=(
                f"{ticket}\n\n"
                f"AI Diagnosis: {result['diagnosis']['diagnosis']}\n\n"
                f"AI Resolution:\n"
                + "\n".join(result["resolution"]["steps"])
                + f"\n\nConfidence: {confidence}%"
            ),
            priority="High",
        )
        response_payload["jira"] = jira_result

        if user_email:
            jira_key = jira_result.get("ticket_id", "ESCALATED")
            email_body = (
                f"Your support ticket has been escalated to our Tier 2 IT Escalation Team.\n\n"
                f"Ticket Details:\n"
                f"- Issue: {ticket}\n"
                f"- Diagnosis: {result['diagnosis']['diagnosis']}\n"
                f"- Category: {result['diagnosis']['category']}\n"
                f"- Confidence Score: {confidence}%\n"
                f"- Jira Tracking Key: {jira_key}\n\n"
                f"Our specialist team is actively reviewing your ticket and will reach out shortly.\n\n"
                f"Regards,\nSupportPilot AI Escalation Desk"
            )
            response_payload["email"] = email_service.send_email(
                user_email,
                f"[SupportPilot] Ticket Escalated to IT Specialist Team ({jira_key})",
                email_body,
            )
        else:
            response_payload["email"] = {
                "success": False,
                "message": "No email provided; skipped escalation notification",
            }

    return jsonify(response_payload)


@app.route("/api/agents/status", methods=["GET"])
@login_required
def api_agents_status():
    """Return status of multi-agent framework components."""
    return jsonify({
        "agents": [
            {"name": "Diagnosis", "status": "Active", "role": "Classify ticket category"},
            {"name": "Retrieval", "status": "Active", "role": "TF-IDF knowledge search"},
            {"name": "Resolution", "status": "Active", "role": "Generate step-by-step fix"},
            {"name": "Validation", "status": "Active", "role": "Confidence scoring"},
            {"name": "Escalation", "status": "Standby", "role": "Route low-confidence to Jira"},
        ],
        "integrations": {
            "jira_configured": bool(
                os.getenv("JIRA_URL") and os.getenv("JIRA_API_TOKEN")
            ),
            "email_configured": bool(
                os.getenv("SMTP_EMAIL") and os.getenv("SMTP_PASSWORD")
            ),
        },
        "milestone": 3,
    })


@app.route("/health")
def health():
    return jsonify({"status": "running", "service": "SupportPilot AI", "milestone": 3})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
