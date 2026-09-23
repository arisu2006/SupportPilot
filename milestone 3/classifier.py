"""
classifier.py
--------------
Loads the trained TF-IDF + Logistic Regression model and exposes
helper functions used by app.py:

    preprocess(text)            -> cleaned text
    predict_category(text)      -> (category, confidence)
    predict_severity(text)      -> severity string
    calculate_priority(sev, bi) -> priority string
    process_ticket(text)        -> category, confidence, severity, priority
"""

import os
import re
import joblib

MODEL_PATH = os.path.join("models", "ticket_classifier.pkl")

_bundle = None


def _load_bundle():
    global _bundle
    if _bundle is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                "Model not found. Run 'python train_model.py' first."
            )
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def preprocess(text: str) -> str:
    """Lowercase, strip punctuation/extra whitespace."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def predict_category(text: str):
    bundle = _load_bundle()
    vectorizer = bundle["vectorizer"]
    model = bundle["model"]

    cleaned = preprocess(text)
    vector = vectorizer.transform([cleaned])
    category = model.predict(vector)[0]

    # confidence = probability of the predicted class
    proba = model.predict_proba(vector)[0]
    confidence = round(float(max(proba)) * 100, 1)

    return category, confidence


def predict_severity(ticket: str) -> str:
    """Simple keyword-based severity engine."""
    text = ticket.lower()

    critical_words = [
        "server down",
        "entire company",
        "production down",
        "security breach",
        "data loss",
    ]
    high_words = [
        "urgent",
        "cannot work",
        "business stopped",
        "client meeting",
        "vpn not working",
        "asap",
        "important meeting",
    ]
    medium_words = [
        "slow",
        "error",
        "problem",
        "issue",
        "not syncing",
    ]

    for word in critical_words:
        if word in text:
            return "Critical"

    for word in high_words:
        if word in text:
            return "High"

    for word in medium_words:
        if word in text:
            return "Medium"

    return "Low"


def calculate_priority(severity: str, business_impact: str = "Medium") -> str:
    if severity == "Critical" and business_impact == "High":
        return "P1"
    elif severity == "High" and business_impact == "High":
        return "P1"
    elif severity == "Critical":
        return "P1"
    elif severity == "High":
        return "P2"
    elif severity == "Medium":
        return "P3"
    else:
        return "P4"


def process_ticket(description: str, business_impact: str = "Medium"):
    """Runs classification + severity + priority in one call."""
    category, confidence = predict_category(description)
    severity = predict_severity(description)
    priority = calculate_priority(severity, business_impact)
    return category, confidence, severity, priority
