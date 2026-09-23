"""
SupportPilot Multi-Agent Resolution Framework (Milestone 3)

Specialized agents collaborate to diagnose, retrieve knowledge,
generate resolution, validate confidence, and escalate difficult tickets.
"""

import json
import os
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# =========================================================
# KNOWLEDGE BASE
# =========================================================
_KB_PATH = os.path.join(
    os.path.dirname(__file__), "knowledge_base", "knowledge.json"
)

with open(_KB_PATH, "r", encoding="utf-8") as file:
    KNOWLEDGE_BASE = json.load(file)


# =========================================================
# 1. DIAGNOSIS AGENT
# =========================================================
class DiagnosisAgent:
    def analyze(self, ticket: str) -> dict:
        text = ticket.lower()
        if any(word in text for word in ["vpn", "network", "internet", "connection"]):
            category = "Network / VPN"
        elif any(word in text for word in ["password", "login", "authentication"]):
            category = "Authentication"
        elif any(word in text for word in ["email", "outlook", "mailbox"]):
            category = "Email"
        elif any(word in text for word in ["printer", "printing", "print"]):
            category = "Printer"
        elif any(word in text for word in ["slow", "performance", "cpu", "memory"]):
            category = "Performance"
        else:
            category = "General IT Issue"

        return {
            "category": category,
            "diagnosis": f"Ticket classified as {category}",
            "confidence": 0.80,
        }


# =========================================================
# 2. RETRIEVAL AGENT
# =========================================================
class RetrievalAgent:
    def __init__(self):
        self.documents = [
            item["title"] + " " + item["content"] for item in KNOWLEDGE_BASE
        ]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(self.documents)

    def search(self, query: str) -> dict:
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix)[0]
        best_index = int(scores.argmax())
        return {
            "article": KNOWLEDGE_BASE[best_index],
            "similarity": float(scores[best_index]),
        }


# =========================================================
# 3. RESOLUTION AGENT
# =========================================================
class ResolutionAgent:
    def generate(self, diagnosis: dict, article: dict) -> dict:
        category = diagnosis["category"]

        if category == "Network / VPN":
            steps = [
                "Check internet connectivity.",
                "Restart the VPN client.",
                "Verify username and password.",
                "Clear the VPN cache.",
                "Restart the computer.",
                "Check firewall and network configuration.",
            ]
        elif category == "Authentication":
            steps = [
                "Open the company password portal.",
                "Select 'Forgot Password'.",
                "Verify employee identity.",
                "Create a new password.",
                "Confirm the new password.",
                "Login again.",
            ]
        elif category == "Email":
            steps = [
                "Check internet connectivity.",
                "Verify mailbox storage.",
                "Restart Outlook.",
                "Remove and re-add the email account.",
                "Verify email server settings.",
            ]
        else:
            # Convert knowledge article into basic steps
            sentences = re.split(r"\. ", article["content"])
            steps = [sentence.strip() for sentence in sentences if sentence.strip()]

        response = (
            f"We identified the issue as {category}. "
            "Please follow these troubleshooting steps:"
        )
        return {
            "response": response,
            "steps": steps,
        }


# =========================================================
# 4. VALIDATION AGENT
# =========================================================
class ValidationAgent:
    def validate(
        self,
        diagnosis_confidence: float,
        retrieval_similarity: float,
        number_of_steps: int,
    ) -> dict:
        # Weighted confidence calculation
        confidence = (
            diagnosis_confidence * 0.40
            + retrieval_similarity * 0.40
            + min(number_of_steps / 6, 1) * 0.20
        )
        confidence = round(confidence * 100, 2)

        if confidence >= 70:
            status = "AUTO_RESOLVE"
        else:
            status = "ESCALATE"

        return {
            "confidence": confidence,
            "status": status,
        }


# =========================================================
# 5. ESCALATION AGENT
# =========================================================
class EscalationAgent:
    def should_escalate(self, validation: dict) -> bool:
        return validation["status"] == "ESCALATE"


# =========================================================
# MULTI-AGENT ORCHESTRATOR
# =========================================================
class SupportPilot:
    def __init__(self):
        self.diagnosis_agent = DiagnosisAgent()
        self.retrieval_agent = RetrievalAgent()
        self.resolution_agent = ResolutionAgent()
        self.validation_agent = ValidationAgent()
        self.escalation_agent = EscalationAgent()

    def process_ticket(self, ticket: str) -> dict:
        # STEP 1: DIAGNOSIS
        diagnosis = self.diagnosis_agent.analyze(ticket)

        # STEP 2: KNOWLEDGE RETRIEVAL
        retrieval = self.retrieval_agent.search(ticket)

        # STEP 3: RESOLUTION GENERATION
        resolution = self.resolution_agent.generate(
            diagnosis, retrieval["article"]
        )

        # STEP 4: VALIDATION
        validation = self.validation_agent.validate(
            diagnosis["confidence"],
            retrieval["similarity"],
            len(resolution["steps"]),
        )

        # STEP 5: ESCALATION CHECK
        escalation = self.escalation_agent.should_escalate(validation)

        return {
            "diagnosis": diagnosis,
            "retrieval": retrieval,
            "resolution": resolution,
            "validation": validation,
            "escalation": escalation,
        }
