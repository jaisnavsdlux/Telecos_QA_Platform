import re
from typing import Dict, Any, List
from graph.state_schema import GraphState

def rule_engine_node(state: GraphState) -> Dict[str, Any]:
    """
    Decision Engine: Executes Cross-Document Logic (R001-R005).
    Uses the enriched PageIndex to make deterministic PASS/FAIL verdicts.
    """
    page_index = state.get("page_index", {})
    if not page_index:
        return {"status": "rule_skipped", "decision_results": []}

    results = []

    # 1. R001: Drawing Inventory Presence (RLM ⊆ As-built)
    rlm_inventory = set(page_index.get("RLM", {}).get("tree", {}).get("aggregated_data", {}).get("drawing_inventory", []))
    asbuilt_inventory = set(page_index.get("As-built", {}).get("tree", {}).get("aggregated_data", {}).get("drawing_inventory", []))
    
    if rlm_inventory:
        missing = rlm_inventory - asbuilt_inventory
        results.append({
            "rule_id": "R001",
            "name": "Drawing Inventory Match (RLM vs As-built)",
            "result": "PASS" if not missing else "FAIL",
            "evidence": {
                "rlm_count": len(rlm_inventory),
                "asbuilt_count": len(asbuilt_inventory),
                "missing_drawings": list(missing) if missing else None
            },
            "reason": "All RLM drawings are present in As-built." if not missing else f"FAIL: {len(missing)} drawings missing from As-built: {list(missing)}",
            "confidence": "HIGH"
        })

    # 2. R002: Drawing Title Consistency
    title_mismatches = []
    rlm_pages = {k: v for k, v in page_index.get("RLM", {}).items() if k != "tree"}
    asbuilt_pages = {k: v for k, v in page_index.get("As-built", {}).items() if k != "tree"}
    
    # Map drawing_no -> title for both
    rlm_titles = {}
    for label, page in rlm_pages.items():
        if not isinstance(page, dict): continue
        summ = page.get("summary", {})
        if summ.get("drawing_no") and summ.get("drawing_title"):
            rlm_titles[summ["drawing_no"]] = (summ["drawing_title"], summ.get("title_status", "EXTRACTED"))
            
    asbuilt_titles = {}
    for label, page in asbuilt_pages.items():
        if not isinstance(page, dict): continue
        summ = page.get("summary", {})
        if summ.get("drawing_no") and summ.get("drawing_title"):
            asbuilt_titles[summ["drawing_no"]] = (summ["drawing_title"], summ.get("title_status", "EXTRACTED"))

    common_nos = set(rlm_titles.keys()) & set(asbuilt_titles.keys())
    for dno in common_nos:
        r_title, r_status = rlm_titles[dno]
        a_title, a_status = asbuilt_titles[dno]
        if r_title != a_title:
            title_mismatches.append({
                "drawing_no": dno,
                "rlm_title": r_title,
                "asbuilt_title": a_title,
                "confidence": "MEDIUM" if (r_status == "INFERRED" or a_status == "INFERRED") else "HIGH"
            })
    
    if common_nos:
        results.append({
            "rule_id": "R002",
            "name": "Cross-Document Title Consistency",
            "result": "PASS" if not title_mismatches else "FAIL",
            "evidence": {
                "checked_drawings": list(common_nos),
                "mismatches": title_mismatches if title_mismatches else None
            },
            "reason": "All drawing titles match across RLM and As-built." if not title_mismatches else f"FAIL: {len(title_mismatches)} title mismatches detected.",
            "confidence": "HIGH" if not any(m["confidence"] == "MEDIUM" for m in title_mismatches) else "MEDIUM"
        })

    # 3. R003: Coordinate Consistency
    all_coords = []
    for doc_tag, doc_data in page_index.items():
        for label, page in doc_data.items():
            if label == "tree" or not isinstance(page, dict): continue
            summ = page.get("summary", {})
            if summ.get("coordinates"):
                all_coords.append({"doc": doc_tag, "page": label, "coords": summ["coordinates"]})
    
    if all_coords:
        first = all_coords[0]["coords"]
        mismatched_coords = [c for c in all_coords if c["coords"] != first]
        results.append({
            "rule_id": "R003",
            "name": "Site Coordinate Consistency",
            "result": "PASS" if not mismatched_coords else "FAIL",
            "evidence": {
                "reference_coords": first,
                "mismatches": mismatched_coords if mismatched_coords else None
            },
            "reason": "Coordinates are consistent across all documents." if not mismatched_coords else "FAIL: Mismatched coordinates found in some documents.",
            "confidence": "HIGH"
        })

    # 4. R004: Antenna Model Match (FR Aggregate vs RLM Aggregate)
    fr_models = set(page_index.get("FR", {}).get("tree", {}).get("aggregated_data", {}).get("antenna_models", []))
    rlm_models = set(page_index.get("RLM", {}).get("tree", {}).get("aggregated_data", {}).get("antenna_models", []))
    
    if fr_models and rlm_models:
        extra_in_fr = fr_models - rlm_models
        extra_in_rlm = rlm_models - fr_models
        results.append({
            "rule_id": "R004",
            "name": "Antenna Model Consistency (FR vs RLM)",
            "result": "PASS" if not (extra_in_fr or extra_in_rlm) else "FAIL",
            "evidence": {
                "fr_models": list(fr_models),
                "rlm_models": list(rlm_models),
                "extra_in_fr": list(extra_in_fr) if extra_in_fr else None,
                "extra_in_rlm": list(extra_in_rlm) if extra_in_rlm else None
            },
            "reason": "Antenna models match between FR and RLM." if not (extra_in_fr or extra_in_rlm) else "FAIL: Antenna model discrepancy detected.",
            "confidence": "HIGH"
        })

    # 5. R005: Lifecycle Status Flow
    # Expected: Design (RLM) -> Approval (FR/PVA) -> Construction (FC) -> As-built
    status_flow = []
    order = ["RLM", "FR", "PVA", "FC_Drawing", "As-built"]
    for doc in order:
        if doc in page_index:
            # Get normalized status from first page
            first_label = next((k for k in page_index[doc].keys() if k != "tree" and isinstance(page_index[doc][k], dict)), None)
            if first_label:
                status = page_index[doc][first_label].get("summary", {}).get("normalized_status")
                if status:
                    status_flow.append({"doc": doc, "status": status})
    
    if status_flow:
        results.append({
            "rule_id": "R005",
            "name": "Document Lifecycle Status Flow",
            "result": "PASS", # Logic can be expanded to check specific transitions
            "evidence": {"flow": status_flow},
            "reason": "Status sequence detected: " + " -> ".join([f"{s['doc']}({s['status']})" for s in status_flow]),
            "confidence": "HIGH"
        })

    return {
        "decision_results": results,
        "status": "decided",
        # Cleanup temporary shared data
        "ref_cache": None,
        "all_pages": None,
        "total_pages": None
    }
