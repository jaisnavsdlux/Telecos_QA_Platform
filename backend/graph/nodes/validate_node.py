import os
import concurrent.futures
from typing import Dict, Any, List
from graph.state_schema import GraphState
from reference_validator.main import _validate_single_rule, _extract_reference_cache, extract_pages

def validate_node(state: GraphState) -> Dict[str, Any]:
    """
    Node: Concurrent rule validation.
    Wraps the rule_engine logic into a graph-compatible node with per-rule token usage tracking.
    """
    pdf_path = state.get("pdf_path")
    active_rules = state.get("active_rules", [])
    ref_mapping = state.get("reference_mapping", {})
    page_map = state.get("page_map", {})
    
    if not active_rules:
        print("[validate] No active rules to process.")
        return {"status": "validated", "validation_results": []}

    target_model = os.getenv("LLM_MODEL", "gemma4:cloud")
    print(f"[validate] Starting validation of {len(active_rules)} rules using model '{target_model}'...")

    # 1. Prepare Reference Cache (text only)
    required_tags = set()
    for r in active_rules:
        for req in r.get("required_references", []):
            required_tags.add(req)
    
    filtered_mapping = {tag: path for tag, path in ref_mapping.items() if tag in required_tags}
    ref_cache = _extract_reference_cache(filtered_mapping)

    # 2. Extract pages for compatibility
    all_pages = [page_map[i] for i in sorted(page_map.keys())] if page_map else []
    if not all_pages and pdf_path:
        all_pages, total_pages = extract_pages(pdf_path)
    else:
        total_pages = len(all_pages)

    # 3. Concurrent Execution (using configurable concurrency)
    concurrency = int(os.getenv("LLM_CONCURRENCY", "3"))
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(
                _validate_single_rule,
                r, all_pages, pdf_path, total_pages, ref_cache, state.get("structured_data"), target_model
            ): r
            for r in active_rules
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                res = future.result()
                if res:
                    results.append(res)
            except Exception as e:
                print(f"[validate] Rule execution failed: {e}")

    # 4. Sort results to maintain deterministic reporting order
    rule_order = {
        (r.get("id") or r.get("rule_id", f"_pos_{i}")): i
        for i, r in enumerate(active_rules)
    }
    results.sort(key=lambda r: rule_order.get(r.get("rule_id", ""), 9999))

    # 5. Extract token logs
    token_logs = [r.get("token_usage") for r in results if r.get("token_usage")]
    total_input = sum(t.get("input_tokens", 0) for t in token_logs)
    total_output = sum(t.get("output_tokens", 0) for t in token_logs)

    print(f"[validate] Validation complete. {len(results)} results gathered. Total input tokens: {total_input}, output tokens: {total_output}.")

    return {
        "validation_results": results,
        "status": "validated",
        "metadata": {
            **state.get("metadata", {}),
            "token_usage_logs": token_logs,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0
        }
    }
