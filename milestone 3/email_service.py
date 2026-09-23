"""
Email Automation Service for SupportPilot Milestone 3.

Sends automated resolution emails to end users when
the multi-agent system auto-resolves a ticket.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email = os.getenv("SMTP_EMAIL")
        self.password = os.getenv("SMTP_PASSWORD")

    def send_email(self, recipient: str, subject: str, body: str) -> dict:
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        email = os.getenv("SMTP_EMAIL")
        password = os.getenv("SMTP_PASSWORD")

        if not email or not password:
            return {
                "success": False,
                "message": "SMTP configuration missing. Set SMTP_EMAIL and SMTP_PASSWORD in .env",
                "simulated": True,
            }

        if not recipient:
            return {
                "success": False,
                "message": "Recipient email is required",
            }

        message = MIMEMultipart()
        message["From"] = email
        message["To"] = recipient
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        try:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=20)
            server.starttls()
            server.login(email, password)
            server.sendmail(email, recipient, message.as_string())
            server.quit()
            return {
                "success": True,
                "message": "Email sent successfully",
            }
        except Exception as error:
            return {
                "success": False,
                "message": str(error),
            }
