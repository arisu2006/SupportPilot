<<<<<<< HEAD
# SupportPilot — Premium AI Support Desk

AI-assisted IT ticket desk with knowledge retrieval, cited resolutions, and JWT auth.

## Features

- **JWT authentication** (PyJWT) — register / login / protected routes
- Premium light dashboard
- Submit ticket → classify + full RAG result **in the same tab**
- Tickets stored in SQLite (`tickets.db`) and listed under **Tickets**
- One-click Google demo sign-in

## Run

```bash
cd SupportPilot_M2
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## JWT (as in the JWT PPT)

| Action | Method | Path | Notes |
|--------|--------|------|--------|
| Register | POST | `/register` or `/api/register` | JSON: `email`/`username`, `password` |
| Login | POST | `/api/login` | Returns `{ "token": "<JWT>" }` |
| Profile | GET | `/profile` or `/api/profile` | Header: `Authorization: Bearer <token>` |
| Me | GET | `/api/auth/me` | Same, cookie or Bearer |

Example:

```bash
# Register
curl -X POST http://127.0.0.1:5000/register -H "Content-Type: application/json" \
  -d '{"username":"saranya","password":"mypassword123","email":"saranya@company.com"}'

# Login → token
curl -X POST http://127.0.0.1:5000/api/login -H "Content-Type: application/json" \
  -d '{"username":"saranya","password":"mypassword123"}'

# Protected profile
curl http://127.0.0.1:5000/profile -H "Authorization: Bearer <token>"
```

UI login also sets an `sp_token` cookie (same JWT).

## Tickets

- Submit from **Submit Ticket** tab → always saved to SQLite
- Classification + RAG workflow + resolution shown **on the same tab**
- **Tickets** tab lists all stored tickets (refreshes after submit)

## API

```
POST /api/ticket          Create + RAG (JWT required)
GET  /api/tickets         List tickets
GET  /api/ticket/<id>     Ticket detail
POST /api/rag             Ad-hoc RAG only
```
=======
# SupportPilot – AI Ticket Resolution Agent

## 🚀 Introduction
**SupportPilot** is an intelligent, AI-powered platform designed to automate IT support-ticket processing, classification, troubleshooting, and resolution workflows. By combining Machine Learning classification, rule-based severity prediction, and Retrieval-Augmented Generation (RAG), SupportPilot streamlines handling repetitive IT requests such as network issues, VPN access failures, password resets, and software installations to significantly reduce resolution time and operational costs[cite: 1, 2].

---

## 📂 Folder Architecture

The project is structured to scale cleanly across milestones, separating core application scripts, RAG pipelines, data sources, and frontend templates:

```text
supportpilot/
│
├── app.py                 # Main Flask web application & REST API endpoints
├── config.py              # Configuration settings and environment variables
├── train_model.py         # Script to train the ticket classification model
├── classifier.py          # Wrapper logic for model prediction and evaluation
├── database.py            # SQLite database initialization and interaction handlers
├── requirements.txt       # Project dependencies and package versions
│
├── data/
│   └── knowledge_base.json# Enterprise knowledge base articles and documentation
│
├── rag/
│   ├── __init__.py
│   ├── analyzer.py        # Ticket text parsing and keyword extraction
│   ├── retriever.py       # TF-IDF / Semantic vector-based knowledge retriever
│   ├── generator.py       # LLM response and troubleshooting step generator
│   └── pipeline.py        # End-to-end RAG orchestrator pipeline
│
├── models/
│   ├── __init__.py
│   ├── schemas.py         # Pydantic or data schemas for ticket payloads
│   └── ticket_classifier.pkl # Serialized machine learning model artifact
│
└── templates/
    └── index.html         # Frontend web UI for ticket submission and tracking
 ```

## 🛠️ Milestones & Core Modules

### Milestone 1 (Weeks 1–2) – Ticket Processing & Classification

* **Ticket Intake:** Accepts and ingests IT support requests via web forms or JSON payloads with fields like employee name, email, title, description, and department[cite: 1].
* **Text Preprocessing:** Cleans ticket text through lowercase conversion, symbol removal, tokenization, and stop-word handling[cite: 1].
* **AI Classification Engine:** Uses TF-IDF vectorization and Logistic Regression models to automatically categorize support issues into classes such as Network, VPN, Password, Software, and Hardware[cite: 1].
* **Severity & Priority Engines:** Automatically predicts issue severity (Low, Medium, High, Critical) and calculates business priorities (P1–P4)[cite: 1].

### Milestone 2 (Weeks 3–4) – Knowledge Retrieval & Resolution Generation

* **Enterprise Knowledge Base Integration:** Connects structured documentation like troubleshooting guides, IT policies, and authentication manuals[cite: 2].
* **Ticket Analysis:** Extracts key technical terms and constructs optimized search queries from ticket contents[cite: 2].
* **RAG Retrieval Engine:** Employs TF-IDF and cosine similarity to search the enterprise knowledge base and find the most relevant articles[cite: 2].
* **Context Augmentation & Generation:** Formats retrieved documents into a secure context window to prompt LLMs for precise, step-by-step troubleshooting solutions with source citations[cite: 2].
>>>>>>> 885aade09bac205dbbb5b2df6b3bc3e36e3c8131
