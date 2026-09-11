"""Ticket analysis — extract keywords and build retrieval query."""

POSSIBLE_KEYWORDS = [
    "vpn",
    "network",
    "firewall",
    "authentication",
    "timeout",
    "connection",
    "dns",
    "password",
    "mfa",
    "outlook",
    "email",
    "sync",
    "hardware",
    "keyboard",
    "monitor",
    "printer",
    "mouse",
    "headset",
    "system",
    "freeze",
    "crash",
    "blue screen",
    "slow",
    "software",
    "license",
    "install",
    "drive",
    "share",
    "login",
    "locked",
]


def analyze_ticket(ticket: dict) -> dict:
    """
    Analyze a support ticket and produce a structured analysis
    used by the retriever.
    """
    title = ticket.get("title") or ""
    description = ticket.get("description") or ""
    text = f"{title} {description}".lower()

    keywords = [kw for kw in POSSIBLE_KEYWORDS if kw in text]

    return {
        "ticket_id": ticket.get("id") or ticket.get("ticket_id"),
        "category": ticket.get("category"),
        "priority": ticket.get("priority"),
        "keywords": keywords,
        "query": text.strip(),
    }
