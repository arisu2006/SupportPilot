"""
train_model.py
----------------
Trains a simple TF-IDF + Logistic Regression classifier that predicts
the category of an IT support ticket (Network, VPN, Password, Software,
Hardware, System), and saves the vectorizer + model to models/ so that
classifier.py can load them at runtime.

Run this once before starting the server:
    python train_model.py
"""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os

# ---------------------------------------------------------------------
# Training data
# A larger, more balanced set than the slide example so the demo model
# generalizes reasonably well across all six categories.
# ---------------------------------------------------------------------
data = {
    "ticket": [
        # Network
        "WiFi is not working",
        "Internet connection is very slow",
        "Unable to connect to office network",
        "Wi-Fi keeps disconnecting every few minutes",
        "Network is down for the entire floor",
        "Ethernet cable not detected on my laptop",
        "Cannot access shared network drive",
        # VPN
        "VPN is not connecting",
        "Unable to access company VPN",
        "VPN keeps dropping during work",
        "Cannot connect to VPN from home",
        "VPN login fails with timeout error",
        "Remote VPN access is not working",
        # Password
        "I forgot my password",
        "Please reset my password",
        "Account locked after multiple login attempts",
        "Unable to log in, password not accepted",
        "Need password reset for email account",
        "Two-factor authentication code not received",
        # Software
        "Install Microsoft Office",
        "Application installation required",
        "Software license has expired",
        "Excel keeps crashing when I open large files",
        "Need access to design software license",
        "Outlook is not syncing emails",
        # Hardware
        "Laptop keyboard is not working",
        "Monitor display is not working",
        "Printer is not responding",
        "Mouse is not detected on my desktop",
        "Laptop battery is not charging",
        "Headset microphone is not working",
        # System
        "Operating system keeps freezing",
        "System is running very slow",
        "Blue screen error on startup",
        "Windows update stuck at installation",
        "System crashes when opening multiple apps",
        "Computer restarts unexpectedly",
    ],
    "category": (
        ["Network"] * 7
        + ["VPN"] * 6
        + ["Password"] * 6
        + ["Software"] * 6
        + ["Hardware"] * 6
        + ["System"] * 6
    ),
}

df = pd.DataFrame(data)


def train_and_save():
    X = df["ticket"]
    y = df["category"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    vectorizer = TfidfVectorizer()
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train_vec, y_train)

    accuracy = accuracy_score(y_test, model.predict(X_test_vec))
    print(f"Validation accuracy on held-out split: {accuracy * 100:.1f}%")

    os.makedirs("models", exist_ok=True)
    joblib.dump(
        {"vectorizer": vectorizer, "model": model},
        os.path.join("models", "ticket_classifier.pkl"),
    )
    print("Saved model to models/ticket_classifier.pkl")


if __name__ == "__main__":
    train_and_save()
