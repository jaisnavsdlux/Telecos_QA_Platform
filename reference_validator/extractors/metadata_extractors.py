import os
import re
from reference_validator.validator.rule_engine import call_llm
from reference_validator.domains.unified_model import SourceValue

PROMPT = """Extract site metadata from the following document text. 
Return ONLY a JSON object with: site_id, site_name, address, work_authority, owner.
If not found, use null."""

def extract_as_built(text: str) -> dict:
    """Extracts authoritative drawing metadata."""
    target_model = os.getenv("LLM_MODEL", "gemma4")
    content = [{"type": "text", "text": text[:10000]}]
    res, _ = call_llm(content, PROMPT, model=target_model, rule_id="EXTRACT_AS_BUILT")
    # Wrap in SourceValue markers
    return {
        k: SourceValue(value=v, source="AS_BUILT")
        for k, v in (res.items() if isinstance(res, dict) else {})
        if v
    }

def extract_rfnsa(text: str) -> dict:
    """Extracts reference site metadata from RFNSA/Client records."""
    target_model = os.getenv("LLM_MODEL", "gemma4")
    content = [{"type": "text", "text": text[:10000]}]
    res, _ = call_llm(content, PROMPT, model=target_model, rule_id="EXTRACT_RFNSA")
    return {
        k: SourceValue(value=v, source="RFNSA")
        for k, v in (res.items() if isinstance(res, dict) else {})
        if v
    }
