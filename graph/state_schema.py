from typing import List, Dict, Any, Optional, Annotated
from typing_extensions import TypedDict
import operator


class GraphState(TypedDict):
    # ── Job Identity ─────────────────────────────────────────────────────────
    job_id: str
    client_id: str                      # e.g. 'optus'

    # ── Mode Routing ─────────────────────────────────────────────────────────
    mode: str                           # 'validate' | 'create_rules'

    # ── ZIP Upload ───────────────────────────────────────────────────────────
    zip_path: str                       # local path of the uploaded ZIP archive
    fc_candidates: List[str]            # filenames inside ZIP classified as FC_Drawing
    selected_fc_name: str               # which FC the user picked (HITL, if multiple)
    excel_checklist_path: str           # local path of an Excel checklist (optional)

    # ── Files ─────────────────────────────────────────────────────────────────
    pdf_path: str
    reference_mapping: Dict[str, str]   # tag → local file path

    # ── Ingested Data ─────────────────────────────────────────────────────────
    extracted_text: str
    page_map: Dict[int, str]
    structured_data: Dict[str, Any]     # LLM-extracted schema from ref docs

    # ── Rules ─────────────────────────────────────────────────────────────────
    active_rules: List[Dict[str, Any]]
    generated_rules: List[Dict[str, Any]]  # DRAFT rules from rule_generator

    # ── Validation Results ────────────────────────────────────────────────────
    # Annotated[..., operator.add] lets parallel validation nodes append safely
    validation_results: Annotated[List[Dict[str, Any]], operator.add]

    # ── Report ────────────────────────────────────────────────────────────────
    report_path: str                    # local path to generated PDF
    report_quality_ok: bool             # set by report_validator auto-check

    # ── Flow Control ──────────────────────────────────────────────────────────
    status: str
    error: str                          # Reason for node failure (if status == 'failed')
    missing_documents: List[str]
    approved: bool                      # Teams HITL approval flag
    human_feedback: str                 # free-text from reviewer

    # ── Analytics / LangSmith ─────────────────────────────────────────────────
    metadata: Dict[str, Any]
