# Reference Validator API (Agentic Version)

A stateful, agentic compliance validation pipeline built on **LangGraph**.
This system automatically extracts digital engineering requirements, processes complex ZIP archives of telecommunication site documents, and uses Anthropic's Claude to enforce structured validation rules.

---

## 🏗️ Architecture & Nodes

The underlying logic is no longer a simple linear script. It runs as a state machine (`GraphState`), allowing us to pause for Human-in-the-Loop interventions and conditionally branch logic.

### Graph Flow:

1. **`zip_upload` (EntryPoint)** 
   - Accepts a ZIP archive containing the For-Construction (FC) drawing and all reference documents (FR, RFNSA, As-built, etc.).
   - Automatically unzips and classifies each file based on its filename.
2. **`mode_router`** 
   - Decides if we are creating rules (`rule_generator`) or running an audit (`fc_selector`).
3. **`ingest`**
   - OCRs the FC Drawing.
   - Triggers Claude with structured output to extract engineering facts directly from the reference documents (FR, RFNSA).
4. **`match_rules`**
   - Scans `clients/optus/rules/*.yaml` and activates rules based on matching keywords in the drawing.
5. **`validate`**
   - Concurrently executes the active rules against the extracted AI context (PASS / FAIL / UNCLEAR verdicts).
6. **`report`** 
   - Compiles validation results into a PDF checklist.
7. **`report_validator`**
   - Quality check branching node (currently defaults to OK).
8. **`human_in_loop`** 
   - **⏸️ Pauses Execution**. Waits for human manual approval or intervention. If rejected/re-run is triggered, it loops back backwards to `validate`!

---

## 🚀 How to Run

You have two powerful tools at your disposal when the development server is running.

Start the LangGraph development server (*this simultaneously serves both the UI and the API*):

```bash
# Ensure your virtual environment is active
.venv\Scripts\activate
.venv\Scripts\langgraph dev
```

### 1. The Visual Approach (LangGraph Studio)
Go to [http://localhost:2024](http://localhost:2024).

1. Click **+ New** on the sidebar to create a Thread.
2. At the bottom left, paste the starting state JSON to trigger a run.
   
**To test with a ZIP archive:**
```json
{
  "job_id": "test-zip-001",
  "client_id": "optus",
  "mode": "validate",
  "zip_path": "jobs/your_upload.zip"
}
```

**To test direct files without zipping:**
```json
{
  "job_id": "test-direct",
  "client_id": "optus",
  "mode": "validate",
  "zip_path": "",
  "pdf_path": "drawings/some_fc.pdf",
  "reference_mapping": {
    "FR": "drawings/fr_doc.pdf",
    "RFNSA": "drawings/rfnsa_doc.pdf"
  }
}
```

When the graph hits `human_in_loop`, it will **pause**. You must click the pink **Resume** button and provide `{"approved": true}` for it to finish and generate the report.

### 2. The API Approach (Swagger / Headless)
Go to [http://localhost:2024/docs](http://localhost:2024/docs)

1. Use **`POST /validate_zip`** to upload your `.zip` file from your desktop. It returns a `job_id`.
2. The LangGraph pipeline will start running automatically in the background.
3. Use **`GET /status/{job_id}`** to poll the progress. Wait until the status changes to `pending_report_review`.
4. Use **`POST /approve_results/{job_id}`** to complete the Human Review step.
5. Use **`GET /report/{job_id}`** to download your finalized PDF report.

*(All of these background executions are fully traced inside LangSmith simultaneously!)*

---

## 🔍 Rule Configuration & Settings

Instead of one monolithic JSON file, rules are natively decoupled.

### `clients/[client_id]/settings.yaml`
Contains universal filters. For example, `cad_only_keywords` suppresses false positives for elements that are hidden inside a PDF but present in the raw CAD.

### `clients/[client_id]/rules/*.yaml`
Each architectural rule is its own YAML file. 
When the `match_rules` node runs, it loops through every rule file. If the `match_keywords` aren't found in the document, the rule is safely skipped. 
Furthermore, the `required_references` block enforces that if a required document (e.g., `FR` or `As-built`) is missing from the ZIP, the specific rule throws a graceful `NOT_APPLICABLE` verdict rather than failing the run.

---

## 🛠️ Tracing & Debugging via LangSmith

Because this is an agentic framework, it generates a full waterfall trace for *every* execution.

Ensure you have your `.env` configured inside the project root:
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT="Telecom-Compliance-Validator"
LANGCHAIN_API_KEY=your_lsv2_key
ANTHROPIC_API_KEY=your_claude_key
```

Navigate to **[smith.langchain.com](https://smith.langchain.com)** to inspect the `Telecom-Compliance-Validator` project.
Within any trace, you can easily debug the full LLM context injection per rule execution, view token consumption, and identify latency bottlenecks directly within the `validate_node`.
