# SupportPilot — Premium AI Support Desk (Milestone 3)

AI-assisted IT ticket desk with **multi-agent workflows**, knowledge retrieval, cited resolutions, JWT auth, **Jira escalation**, and **email automation**.

## 🏁 Milestones & Core Modules

▼ 🧩 **Milestone 1 (Weeks 1–2) — Ticket Processing & Classification**
- **Ticket Intake** — Accepts and ingests IT support requests via web forms or JSON payloads with fields like employee name, email, title, description, and department
- **Text Preprocessing** — Cleans ticket text through lowercase conversion, symbol removal, tokenization, and stop-word handling
- **AI Classification Engine** — Uses TF-IDF vectorization and Logistic Regression to automatically categorize issues into Network, VPN, Password, Software, and Hardware
- **Severity & Priority Engine** — Automatically predicts issue severity (Low / Medium / High) and calculates business priority (P1–P4)

▼ 📚 **Milestone 2 (Weeks 3–4) — Knowledge Retrieval & Resolution Generation**
- **Enterprise Knowledge Base Integration** — Connects structured documentation like troubleshooting guides, IT policies, and authentication manuals
- **Ticket Analysis** — Extracts key technical terms and constructs optimized search queries from ticket contents
- **RAG Retrieval Engine** — Employs TF-IDF and cosine similarity to search the knowledge base and surface the most relevant articles
- **Context Augmentation & Generation** — Formats retrieved documents into a secure context window to prompt an LLM for precise, step-by-step troubleshooting with source citations

▼ 🤖 **Milestone 3 (Weeks 5–6) — Multi-Agent Workflows & Integrations**
- **Agent Orchestration Pipeline** — Coordinates specialized, single-purpose AI agents (Diagnosis, Retrieval, Resolution, Validation, Escalation) into a cohesive troubleshooting workflow
- **Confidence Scoring Validation** — Dynamically evaluates resolution quality through a weighted formula combining category match rate, semantic search similarity, and step completeness
- **Automated ITSM Routing (Jira Integration)** — Intercepts low-confidence resolutions (&lt; 70%) and automatically escalates them to a Jira board via REST API
- **User Communication (Email Automation)** — Actively dispatches SMTP emails containing self-service guides when agents achieve an AUTO_RESOLVE status
- **Interactive 3D Dashboard** — Provides a real-time, full-screen UI displaying agent telemetry, status pills, and integration health states using responsive vector SVGs

## Project Structure

```
SupportPilot_M2/
├── agents.py              # Multi-agent framework (Diagnosis, Retrieval, Resolution, Validation, Escalation)
├── jira_service.py        # Jira REST API client
├── email_service.py       # SMTP email automation
├── knowledge_base/
│   └── knowledge.json     # Retrieval agent knowledge repository
├── app.py                 # Flask backend (RAG + multi-agent APIs)
├── auth.py / classifier.py / database.py
├── rag/                   # Existing RAG pipeline
├── templates/
│   ├── index.html         # Main dashboard
│   ├── login.html
│   └── multi_agent.html   # Milestone 3 agent dashboard
├── static/
├── requirements.txt
└── .env.example
```

## Setup

```bash
cd SupportPilot_M2
pip install -r requirements.txt
cp .env.example .env
# Edit .env with optional Jira / SMTP credentials
python app.py
```

Open http://127.0.0.1:5000

## Environment Variables

```env
# Flask / JWT
JWT_SECRET=change-this-to-a-long-random-string
JWT_EXPIRE_HOURS=24
FLASK_SECRET=another-long-random-string

# Jira (optional – used on ESCALATE)
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=IT

# Email / SMTP (optional – used on AUTO_RESOLVE)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=support@example.com
SMTP_PASSWORD=your-app-password
```

If Jira/SMTP are not configured, the system still runs and returns simulated/status messages.

## Multi-Agent API

| Action | Method | Path | Notes |
|--------|--------|------|--------|
| Process ticket | POST | `/api/multi-agent` | Body: `{ "ticket": "...", "email": "..." }` |
| Agent status | GET | `/api/agents/status` | Lists agents + integration flags |
| Multi-agent UI | GET | `/multi-agent` | Browser dashboard |
| Health | GET | `/health` | Service health |

### Example flow

```bash
# After login (cookie or Bearer token)

curl -X POST http://127.0.0.1:5000/api/multi-agent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"ticket":"My VPN is not connecting to the company network.","email":"user@company.com"}'
```

**High confidence (≥70%)** → `AUTO_RESOLVE` + optional email  
**Low confidence (&lt;70%)** → `ESCALATE` + Jira ticket creation

### Confidence formula

```
confidence = diagnosis×0.40 + retrieval_similarity×0.40 + min(steps/6,1)×0.20
```

## Existing APIs (Milestone 2)

```
POST /api/ticket          Create + RAG (JWT required)
GET  /api/tickets         List tickets
GET  /api/ticket/<id>     Ticket detail
POST /api/rag             Ad-hoc RAG only
POST /register            Register user
POST /api/login           Login → JWT
```

## How the Multi-Agent System Works

1. **Diagnosis Agent** — keyword rules → category + 80% base confidence  
2. **Retrieval Agent** — TF-IDF search over `knowledge_base/knowledge.json`  
3. **Resolution Agent** — category-specific or article-derived steps  
4. **Validation Agent** — weighted confidence → AUTO_RESOLVE or ESCALATE  
5. **Escalation Agent** — triggers Jira when status is ESCALATE  

This is **not one large AI function** — independent agents coordinate via the `SupportPilot` orchestrator.
