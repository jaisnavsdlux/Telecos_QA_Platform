import os
import json
import re
import traceback
import pandas as pd
import fitz  # PyMuPDF
import requests
import concurrent.futures
import base64
from reference_validator.main import extract_rules_from_checklist
from reference_validator.validator.rule_engine import call_llm

def _encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
        
def _find_matching_image(image_text: str, image_paths: list[str]) -> str | None:
    if not image_text or not image_paths:
        return None
    for p in image_paths:
        req_core = "".join(c for c in image_text.split('.')[0].lower() if c.isalnum())
        up_core = "".join(c for c in os.path.basename(p).split('.')[0].lower() if c.isalnum())
        if req_core and up_core and (req_core in up_core or up_core in req_core):
            return p
    return None

def __save_to_cache(file_hash: str, rules: list):
    cache_path = "jobs/rule_cache.json"
    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            try:
                cache = json.load(f)
            except Exception:
                pass
    cache[file_hash] = rules
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=4)

def call_llm_for_rule(check_name: str, images_data: list[dict] | None = None) -> dict | None:
    """
    images_data: list of {'base64': str, 'media_type': str}
    """
    system_prompt = """You are an expert Rule Generation Agent for a TELECOM ENGINEERING compliance validator.
You generate structured JSON rules used to automatically validate For-Construction (FC) drawings
for 5G rollout projects in Australia and the UK (clients: Optus, Vodafone, Telstra).

Return ONLY valid JSON matching this schema:
{
  "name": "...",
  "type": "high | medium | low",
  "match_keywords": ["..."],
  "validation_mode": "auto | llm_only | cad_only",
  "description": "...",
  "scope": "...",
  "pass_criteria": "...",
  "fail_criteria": "...",
  "expected_patterns": ["..."],
  "negative_constraints": ["..."],
  "required_references": ["..."],
  "deterministic_checks": []
}
"""
    content = [{"type": "text", "text": f"Generate a JSON rule for the following engineering check. Please refer to the PROVIDED IMAGES (if any) as the standard for what a PASS looks like.\n\nCheck Name: {check_name}"}]
    
    if images_data:
        for img in images_data:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": img['media_type'],
                    "data": img['base64']
                }
            })
            
    target_model = os.getenv("LLM_MODEL", "gemma4")
    try:
        raw_res, token_usage = call_llm(content, system_prompt, model=target_model, rule_id="RULE_GEN")
        if isinstance(raw_res, dict) and (raw_res.get("name") or raw_res.get("description")):
            return raw_res
        return None
    except Exception as e:
        print(f"Error generating rule: {e}")
        return None

def _generate_single_rule(index: int, rule: dict, image_paths: list[str], rule_image_map: dict | None = None) -> dict | None:
    check_name = rule.get("rule_text", "")
    if not check_name or check_name.lower().strip() in ["check name", "check", "rule", ""]:
        return None
        
    rule_key = rule.get("rule_key")
    required_filenames = rule_image_map.get(rule_key, []) if rule_image_map else []
    
    images_to_send = []
    
    for req_fn in required_filenames:
        matching_image_path = _find_matching_image(req_fn, image_paths)
        if matching_image_path:
            b64 = _encode_image(matching_image_path)
            m_type = "image/png" if matching_image_path.lower().endswith(".png") else "image/jpeg"
            images_to_send.append({"base64": b64, "media_type": m_type})
            
    rule_json = call_llm_for_rule(check_name, images_to_send)
    if rule_json:
        rule_json["_sort_index"] = index
        rule_json["id"] = f"DRAFT_R{index:03d}"
        return rule_json
    return None

def generate_rules_job(job_id: str, excel_path: str, already_jsonified: list[dict], new_rules: list[dict], image_paths: list[str], jobs_dict: dict, file_hash: str | None = None, force_refresh: bool = False, rule_image_map: dict | None = None):
    try:
        print(f"[agent:{job_id}] START — already_jsonified={len(already_jsonified)}, new_rules={len(new_rules)}, images={len(image_paths)}")
        generated_rules = []
        
        # 0. Check cache if not forcing refresh
        cache_path = "jobs/rule_cache.json"
        if not force_refresh and file_hash and os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                try:
                    cache = json.load(f)
                    if file_hash in cache:
                        print(f"[agent:{job_id}] Cache HIT — returning cached rules")
                        jobs_dict[job_id]["status"] = "pending_rule_review"
                        jobs_dict[job_id]["generated_rules"] = cache[file_hash]
                        return
                except Exception as ce:
                    print(f"[agent:{job_id}] Cache read error: {ce}")

        # 1. Add already jsonified rules immediately
        print(f"[agent:{job_id}] Step 1: Adding {len(already_jsonified)} existing rules")
        for r in already_jsonified:
            generated_rules.append(r)
            
        # 2. Run LLM exclusively on NEW rules
        print(f"[agent:{job_id}] Step 2: Sending {len(new_rules)} new rules to LLM")

        new_generated = []
        concurrency = int(os.getenv("LLM_CONCURRENCY", "3"))
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(_generate_single_rule, i, r, image_paths, rule_image_map) for i, r in enumerate(new_rules)]
            for future in concurrent.futures.as_completed(futures):
                try:
                    res = future.result()
                    if res:
                        new_generated.append(res)
                except Exception as fe:
                    print(f"[agent:{job_id}] Future error: {fe}")
                    
        print(f"[agent:{job_id}] Step 2 done — {len(new_generated)} rules generated by LLM")

        # Restore original order of new rules
        new_generated.sort(key=lambda x: x.get("_sort_index", 0))
        for r in new_generated:
            r.pop("_sort_index", None)
            generated_rules.append(r)

        print(f"[agent:{job_id}] DONE — total generated_rules={len(generated_rules)}. Setting status=pending_rule_review")
        jobs_dict[job_id]["status"] = "pending_rule_review"
        jobs_dict[job_id]["generated_rules"] = generated_rules
        
        if file_hash:
            __save_to_cache(file_hash, generated_rules)
            
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[agent:{job_id}] FATAL ERROR: {e}\n{tb}")
        jobs_dict[job_id]["status"] = "failed"
        jobs_dict[job_id]["error"] = f"{e}\n\nTraceback:\n{tb}"

def regenerate_rules_job(job_id: str, feedback: str, jobs_dict: dict, file_hash: str | None = None):
    try:
        job = jobs_dict[job_id]
        job["status"] = "pending_rule_review"
    except Exception as e:
        jobs_dict[job_id]["status"] = "failed"
        jobs_dict[job_id]["error"] = str(e)
