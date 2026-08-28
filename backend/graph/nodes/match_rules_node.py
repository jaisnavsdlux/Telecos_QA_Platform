import os
import yaml
from typing import Dict, Any, List
from graph.state_schema import GraphState

def match_rules_node(state: GraphState) -> Dict[str, Any]:
    """
    Node: Compare extracted text against rule keywords to identify active rules.
    Also identifies missing documents based on active rule requirements.
    """
    client_id = state.get("client_id", "optus")
    extracted_text = state.get("extracted_text", "").lower()
    ref_mapping = state.get("reference_mapping", {})
    
    rules_dir = os.path.join("clients", client_id, "rules")
    if not os.path.exists(rules_dir):
        return {"status": "failed", "error": f"Rules directory not found: {rules_dir}"}

    print(f"[match_rules] Scanning for active rules in {rules_dir}")
    
    active_rules = []
    missing_docs = set()
    
    # Process each Atomic YAML file
    for filename in os.listdir(rules_dir):
        if filename.endswith(".yaml"):
            with open(os.path.join(rules_dir, filename), "r", encoding="utf-8") as f:
                rule = yaml.safe_load(f)
                if not rule: continue
                
                print(f"[match_rules] Loaded {filename} (ID: {rule.get('id')})")
                
                # Rule Activation Logic (Forced unconditionally)
                match_keywords = rule.get("match_keywords", [])
                
                # We force it to be active to run every rule every time
                is_active = True
                
                # Skip rules per user request
                if rule.get("validation_mode") == "cad_only":
                    continue
                if "google map" in str(rule).lower():
                    continue

                if is_active:
                    active_rules.append(rule)
                    # Check for missing required references
                    req_refs = rule.get("required_references", [])
                    for ref in req_refs:
                        if ref not in ref_mapping:
                            missing_docs.add(ref)

    print(f"[match_rules] Identified {len(active_rules)} active rules.")
    if missing_docs:
        print(f"[match_rules] Missing documents detected: {list(missing_docs)}")

    return {
        "active_rules": active_rules,
        "missing_documents": sorted(list(missing_docs)),
        "status": "rules_matched"
    }
