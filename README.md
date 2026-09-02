# 🚀 Strelza Telecos QA Platform — Phase 1 Enterprise Build

> **AI-Powered Multi-Modal Compliance Audit Suite for Telecom "For-Construction" CAD Drawings**  
> *Engineered for Tier-1 Telecommunications Infrastructure (Optus & Australian Telco Standards)*

---

## 📋 Executive Overview

The **Strelza Telecos QA Platform** automates the comprehensive engineering quality assurance process for cellular tower site drawings. 

Prior to field deployment, every For-Construction (FC) drawing package must be cross-verified against multiple independent companion engineering documents (e.g., Structural Certificates, Lease Plans, Detailed Plumbing Diagrams, Equipment Specifications, and OSD Safety Standards).

Our platform replaces manual 5-hour QA reviews with an **automated, evidence-backed multi-modal AI audit** across **72 codified compliance rules** in under 15 minutes.

---

## 🏗️ Core Architecture & Capabilities

```mermaid
graph LR
    A["Frontend Web Interface<br/>(SPA / Dashboard / Visualizer)"] -->|REST API| B["FastAPI Backend Service<br/>(Uvicorn Core)"]
    B --> C["72-Rule Compliance Engine<br/>(Optus BA Standards)"]
    C --> D["Anthropic Claude API<br/>(claude-opus-5 / Vision & Text)"]
    C --> E["PyMuPDF Vector Parser<br/>(Tabular Layout & Coordinates)"]
    B --> F["JIT Lifecycle Memory Guard<br/>(Sub-180MB RAM Footprint)"]
    B --> G["ReportLab PDF Generator<br/>(Formal Multi-Page Audit Reports)"]
    B --> H["Neon PostgreSQL / Local DB<br/>(Persistent Run Telemetry)"]
```

* **Multi-Modal AI Engine:** Powered by **Anthropic Claude (`claude-opus-5` / `claude-3-7-sonnet`)** for combined computer vision analysis and deep technical reasoning.
* **Evidence-Backed Verification:** Every PASS / FAIL verdict is accompanied by quoted verbatim text, exact page/coordinate citations, and remediation steps.
* **Just-In-Time (JIT) Memory Guard:** Reference files reside safely on disk (0 MB RAM) and are opened into memory only for ~1.5 seconds per rule check, ensuring enterprise stability in memory-constrained environments.
* **Multi-Page Visualizer & Reporting:** Generates signed, publication-ready PDF compliance reports with interactive in-browser preview at 150 DPI.

---

## ⚡ Quick Start: 3 Ways to Run

### 🔹 Option 1: Standalone Executable JAR (Recommended)
If you have Java 11+ installed:

```bash
# Launch the platform
java -jar strelza_phase_one.jar

# Or inspect build version & help
java -jar strelza_phase_one.jar --version
java -jar strelza_phase_one.jar --help
```

---

### 🔹 Option 2: 1-Click OS Launchers

* **On Windows:**  
  Double-click **`start.bat`** (or run `.\start.bat` in PowerShell/CMD).
* **On macOS / Linux:**  
  ```bash
  chmod +x start.sh
  ./start.sh
  ```

---

### 🔹 Option 3: Direct Python Runner

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python run_app.py
```

Once started, open your web browser at:
👉 **`http://localhost:8000/static/index.html`** (or **`http://localhost:8000/static/dashboard.html`**)

---

## 🔑 Setting Up Your Claude API Key

The platform uses Anthropic Claude for multi-modal reasoning and CAD visual inspection.

### Automatic Interactive Setup:
When you run `python run_app.py` or `start.bat` for the first time, the launcher will prompt you:
```text
👉 Enter your Anthropic Claude API Key: sk-ant-api03-...
```
It will automatically save the key to `.env` for all future sessions.

### Manual Setup via `.env` File:
Create or edit a `.env` file in the project folder with:
```env
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-api-key-here
LLM_MODEL=claude-opus-5
PORT=8000
HOST=0.0.0.0
```

---

## 🖥️ Platform Tour & Workflows

| Navigation Tab | Purpose | Key Features |
| :--- | :--- | :--- |
| **1. Dashboard** | Executive Site Telemetry | Compliance Score %, Total Pass/Fail counts, Token consumption metrics, Site metadata (`H8097` Austins Ferry). |
| **2. Package & Reference Area** | Engineering Asset Hub | Multi-project workspace selector, CAD drawing ingestion, and automated classification of all 18 reference files (`SP1_Certificate`, `Lease_Plan`, `DPD`, `Equipment_Specs`, `Pole_Certificate`, `OSD`). |
| **3. Checkpoint Validation** | 72-Rule Compliance Engine | Real-time live audit progress stream, expandable verdict cards with cited verbatim evidence quotes and confidence ratings. |
| **4. Audit Reports Hub** | Executive Report Archive | LIFO report stack (latest on top), high-resolution in-browser multi-page PDF rendering at 150 DPI, and 1-click PDF download. |

---

## 🧪 Verification & Health Testing

To verify the installation and all backend services:

```bash
# Test backend health
curl http://localhost:8000/api/health

# Test rule catalog
curl http://localhost:8000/api/checkpoints?project_id=H8097

# Test active projects
curl http://localhost:8000/api/projects
```

---

## 📁 Repository & Package Layout

```text
strelza_phase_one/
├── strelza_phase_one.jar      # Portable standalone executable JAR package
├── start.bat                  # 1-Click Windows Launcher
├── start.sh                   # 1-Click Linux / macOS Launcher
├── run_app.py                 # Master Application Entrypoint
├── requirements.txt           # Python Production Dependencies
├── README.md                  # Executive Walkthrough & Documentation
├── backend/                   # FastAPI Backend Services & Rule Engines
│   ├── main.py                # Server initialization & API middleware
│   ├── config.py              # Centralized environment & storage configuration
│   ├── reference_validator/   # 72-Rule AI validation & multi-modal arbitration
│   ├── services/              # Project, report, and storage services
│   ├── routers/               # Modular REST endpoints (projects, reports, telemetry)
│   └── qaInput/               # Primary CAD drawing & 18 reference documents
├── frontend/                  # Web Interface HTML, CSS, & JS templates
├── static/                    # High-contrast UI styling, icons, and components
└── clients/                   # 72 YAML-defined Optus BA rule schemas
```

---

## 🛡️ Security, Governance & Compliance

* **Data Isolation:** Every project workspace (`H8097`) is completely isolated on disk with independent reference mappings and report archives.
* **Deterministic Guardrails:** Semantic AI outputs are verified through regex tolerance arbitrations to eliminate hallucinations.
* **CORS & Authentication:** Enterprise session handling with role-based admin access control.

---
*Developed by Strelza Engineering.*
