"""
Jira Integration Service for SupportPilot Milestone 3.

Creates Jira issues when the multi-agent system escalates
low-confidence tickets.
"""

import os
import requests
from requests.auth import HTTPBasicAuth


class JiraService:
    def __init__(self):
        self.url = os.getenv("JIRA_URL")
        self.email = os.getenv("JIRA_EMAIL")
        self.api_token = os.getenv("JIRA_API_TOKEN")
        self.project_key = os.getenv("JIRA_PROJECT_KEY")

    def create_ticket(self, summary: str, description: str, priority: str = "High") -> dict:
        url = os.getenv("JIRA_URL")
        email = os.getenv("JIRA_EMAIL")
        api_token = os.getenv("JIRA_API_TOKEN")
        project_key = os.getenv("JIRA_PROJECT_KEY")

        if not all([url, email, api_token, project_key]):
            return {
                "success": False,
                "message": "Jira configuration not available. Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY in .env",
                "simulated": True,
                "ticket_id": "IT-SIM-001",
            }

        endpoint = f"{url.rstrip('/')}/rest/api/3/issue"

        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary[:255],
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "text": description[:3000],
                                    "type": "text",
                                }
                            ],
                        }
                    ],
                },
                "issuetype": {"name": "Task"},
                "priority": {"name": priority},
            }
        }

        try:
            response = requests.post(
                endpoint,
                json=payload,
                auth=HTTPBasicAuth(email, api_token),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=20,
            )
        except requests.RequestException as exc:
            return {
                "success": False,
                "message": f"Jira request failed: {exc}",
            }

        if response.status_code in (200, 201):
            data = response.json()
            return {
                "success": True,
                "ticket_id": data.get("key"),
                "message": "Jira ticket created successfully",
            }

        return {
            "success": False,
            "message": response.text[:500] if response.text else f"HTTP {response.status_code}",
        }
