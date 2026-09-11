
# SupportPilot – AI Ticket Resolution Agent
  AI-assisted IT ticket desk with knowledge retrieval, cited resolutions, and JWT auth.
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

* **Ticket Intake:** Accepts and ingests IT support requests via web forms or JSON payloads with fields like employee name, email, title, description, and department
* **Text Preprocessing:** Cleans ticket text through lowercase conversion, symbol removal, tokenization, and stop-word handling
* **AI Classification Engine:** Uses TF-IDF vectorization and Logistic Regression models to automatically categorize support issues into classes such as Network, VPN, Password, Software, and Hardware
* **Severity & Priority Engines:** Automatically predicts issue severity (Low, Medium, High, Critical) and calculates business priorities (P1–P4)

### Milestone 2 (Weeks 3–4) – Knowledge Retrieval & Resolution Generation

* **Enterprise Knowledge Base Integration:** Connects structured documentation like troubleshooting guides, IT policies, and authentication manuals
* **Ticket Analysis:** Extracts key technical terms and constructs optimized search queries from ticket contents
* **RAG Retrieval Engine:** Employs TF-IDF and cosine similarity to search the enterprise knowledge base and find the most relevant articles
* **Context Augmentation & Generation:** Formats retrieved documents into a secure context window to prompt LLMs for precise, step-by-step troubleshooting solutions with source citations
