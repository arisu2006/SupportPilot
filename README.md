<div align="center">

![Header](https://capsule-render.vercel.app/api?type=waving&color=0:1e0030,50:6a00f4,100:00d4ff&height=150&section=header&text=SupportPilot&fontSize=46&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=AI%20Ticket%20Resolution%20Agent&descAlignY=58&descSize=18)

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=20&pause=1000&color=B266FF&center=true&vCenter=true&width=650&lines=AI-Assisted+IT+Ticket+Desk;Knowledge+Retrieval+%2B+RAG+Pipeline;Cited+Resolutions+%7C+JWT+Auth)](https://git.io/typing-svg)

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)

</div>

---

### 🚀 Introduction

**SupportPilot** is an intelligent, AI-powered platform that automates IT support ticket processing, classification, troubleshooting, and resolution workflows. By combining machine-learning classification, rule-based severity prediction, and **Retrieval-Augmented Generation (RAG)**, SupportPilot handles repetitive IT requests — network issues, VPN failures, password resets, software installs — cutting resolution time and operational cost.

---

### 📁 Folder Architecture

```
supportpilot/
├── app.py                   # Main Flask web application & REST API endpoints
├── config.py                 # Configuration settings and environment variables
├── train_model.py             # Script to train the ticket classification model
├── classifier.py               # Wrapper logic for model prediction and evaluation
├── database.py                  # SQLite database initialization and interaction handlers
├── requirements.txt              # Project dependencies and package versions
│
├── data/
│   └── knowledge_base.json        # Enterprise knowledge base articles and documentation
│
├── rag/
│   ├── __init__.py
│   ├── analyzer.py                 # Ticket text parsing and keyword extraction
│   ├── retriever.py                 # TF-IDF / semantic vector-based knowledge retriever
│   ├── generator.py                  # LLM response and troubleshooting step generator
│   └── pipeline.py                    # End-to-end RAG orchestrator pipeline
│
├── models/
│   ├── __init__.py
│   ├── schemas.py                      # Pydantic / data schemas for API payloads
│   └── ticket_classifier.pkl            # Serialized machine learning model artifact
│
└── templates/
    └── index.html                       # Frontend web UI for ticket submission and tracking
```

---

### 🏁 Milestones & Core Modules

<details open>
<summary><b>🧩 Milestone 1 (Weeks 1–2) — Ticket Processing & Classification</b></summary>
<br>

- **Ticket Intake** — Accepts and ingests IT support requests via web forms or JSON payloads with fields like employee name, email, title, description, and department
- **Text Preprocessing** — Cleans ticket text through lowercase conversion, symbol removal, tokenization, and stop-word handling
- **AI Classification Engine** — Uses TF-IDF vectorization and Logistic Regression to automatically categorize issues into Network, VPN, Password, Software, and Hardware
- **Severity & Priority Engine** — Automatically predicts issue severity (Low / Medium / High) and calculates business priority (P1–P4)

</details>

<details open>
<summary><b>📚 Milestone 2 (Weeks 3–4) — Knowledge Retrieval & Resolution Generation</b></summary>
<br>

- **Enterprise Knowledge Base Integration** — Connects structured documentation like troubleshooting guides, IT policies, and authentication manuals
- **Ticket Analysis** — Extracts key technical terms and constructs optimized search queries from ticket contents
- **RAG Retrieval Engine** — Employs TF-IDF and cosine similarity to search the knowledge base and surface the most relevant articles
- **Context Augmentation & Generation** — Formats retrieved documents into a secure context window to prompt an LLM for precise, step-by-step troubleshooting with source citations


 🤖 **Milestone 3 (Weeks 5–6) — Multi-Agent Workflows & Integrations**
- **Agent Orchestration Pipeline** — Coordinates specialized, single-purpose AI agents (Diagnosis, Retrieval, Resolution, Validation, Escalation) into a cohesive troubleshooting workflow
- **Confidence Scoring Validation** — Dynamically evaluates resolution quality through a weighted formula combining category match rate, semantic search similarity, and step completeness
- **Automated ITSM Routing (Jira Integration)** — Intercepts low-confidence resolutions (&lt; 70%) and automatically escalates them to a Jira board via REST API
- **User Communication (Email Automation)** — Actively dispatches SMTP emails containing self-service guides when agents achieve an AUTO_RESOLVE status
- **Interactive 3D Dashboard** — Provides a real-time, full-screen UI displaying agent telemetry, status pills, and integration health states using responsive vector SVGs


</details>

---

<div align="center">

![Footer](https://capsule-render.vercel.app/api?type=waving&color=0:00d4ff,50:6a00f4,100:1e0030&height=110&section=footer)

</div>
