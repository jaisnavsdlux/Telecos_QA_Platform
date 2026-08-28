import json
import re
from pathlib import Path
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────
KB_DIR     = Path(__file__).parent / "knowledge_base"
PASS_FILE  = KB_DIR / "pass.md"
FAIL_FILE  = KB_DIR / "fail.md"
UNCLEAR_FILE = KB_DIR / "unclear.md"

VERDICT_FILE_MAP = {
    "PASS":    PASS_FILE,
    "FAIL":    FAIL_FILE,
    "UNCLEAR": UNCLEAR_FILE,
}


def init_kb():
    """Create knowledge base folder and files if they don't exist."""
    KB_DIR.mkdir(exist_ok=True)

    headers = {
        PASS_FILE:    "# PASS Knowledge Base\n\nAll rules that have returned PASS verdict.\nAuto-updated after every validation run.\n\n---\n\n",
        FAIL_FILE:    "# FAIL Knowledge Base\n\nAll rules that have returned FAIL verdict.\nAuto-updated after every validation run.\n\n---\n\n",
        UNCLEAR_FILE: "# UNCLEAR Knowledge Base\n\nAll rules that have returned UNCLEAR verdict.\nAuto-updated after every validation run.\n\n---\n\n",
    }

    for filepath, header in headers.items():
        if not filepath.exists():
            filepath.write_text(header, encoding="utf-8")

    print("  📚 Knowledge base initialised")


def _parse_existing_entry(content: str, rule_id: str) -> dict | None:
    """
    Parse existing entry for a rule_id from markdown content.
    Returns dict with times_seen and confidence if found.
    """
    pattern = rf"## {rule_id} —.*?\n(.*?)(?=\n## |\Z)"
    match   = re.search(pattern, content, re.DOTALL)

    if not match:
        return None

    block = match.group(0)

    times_seen  = 1
    confidence  = 0.5

    times_match = re.search(r"\*\*Times seen:\*\* (\d+)", block)
    conf_match  = re.search(r"\*\*Confidence:\*\* ([\d.]+)", block)

    if times_match:
        times_seen = int(times_match.group(1))
    if conf_match:
        confidence = float(conf_match.group(1))

    return {
        "times_seen": times_seen,
        "confidence": confidence,
        "block":      block
    }


def _calculate_confidence(old_confidence: float, times_seen: int,
                           same_verdict: bool) -> float:
    """
    Confidence increases when same verdict is seen consistently.
    Drops when verdict changes (conflicting evidence).
    """
    if same_verdict:
        return round(min(0.99, old_confidence + (0.05 / max(times_seen, 1))), 3)
    else:
        return round(max(0.30, old_confidence - 0.15), 3)


def update_knowledge_base(results: list, pdf_path: str, rule_image_map: dict):
    """
    Auto-updates knowledge base markdown files after every validation run.
    Called automatically at the end of run_reference_validation.

    Args:
        results:       list of verdict dicts from validation run
        pdf_path:      path to the FC drawing PDF
        rule_image_map: RULE_IMAGE_MAP from reference_validator.py
    """
    init_kb()

    drawing_name = Path(pdf_path).name
    run_date     = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Group results by verdict
    grouped = {"PASS": [], "FAIL": [], "UNCLEAR": []}
    for r in results:
        verdict = r.get("verdict", "UNCLEAR")
        if verdict in grouped:
            grouped[verdict].append(r)

    # Update each verdict file
    for verdict_type, verdict_results in grouped.items():
        if not verdict_results:
            continue

        filepath = VERDICT_FILE_MAP[verdict_type]
        content  = filepath.read_text(encoding="utf-8")

        for r in verdict_results:
            rule_id   = r.get("rule_id", "")
            rule_text = r.get("rule_text", "")
            evidence  = r.get("evidence", "")
            rule_info = rule_image_map.get(rule_id, {})
            ref_image = rule_info.get("image", "N/A")
            pages     = rule_info.get("pages", [])

            existing = _parse_existing_entry(content, rule_id)

            if existing:
                # Rule exists — update counts and confidence
                times_seen     = existing["times_seen"] + 1
                same_verdict   = True  # same file = same verdict type
                new_confidence = _calculate_confidence(
                    existing["confidence"], times_seen, same_verdict
                )

                new_block = _build_entry(
                    rule_id, rule_text, drawing_name, run_date,
                    pages, evidence, ref_image,
                    times_seen, new_confidence, verdict_type
                )

                # Replace old block with updated block
                content = content.replace(existing["block"], new_block)

            else:
                # New rule — append to file
                new_block = _build_entry(
                    rule_id, rule_text, drawing_name, run_date,
                    pages, evidence, ref_image,
                    1, 0.50, verdict_type
                )
                content += new_block

        filepath.write_text(content, encoding="utf-8")
        print(f"  📝 knowledge_base/{verdict_type.lower()}.md updated "
              f"({len(verdict_results)} rules)")


def _build_entry(rule_id: str, rule_text: str, drawing_name: str,
                 run_date: str, pages: list, evidence: str,
                 ref_image: str, times_seen: int,
                 confidence: float, verdict: str) -> str:
    """Build a single markdown entry block."""

    # Confidence label
    if confidence >= 0.85:
        conf_label = "🟢 High"
    elif confidence >= 0.60:
        conf_label = "🟡 Medium"
    else:
        conf_label = "🔴 Low"

    pages_str = ", ".join(str(p) for p in pages) if pages else "N/A"

    return f"""## {rule_id} — {rule_text}
- **Verdict:** {verdict}
- **Drawing:** {drawing_name}
- **Last seen:** {run_date}
- **Pages checked:** {pages_str}
- **Reference image:** {ref_image}
- **Evidence:** {evidence}
- **Times seen:** {times_seen}
- **Confidence:** {confidence} {conf_label}

---

"""


def query_knowledge_base(rule_id: str, verdict_type: str = None,
                         threshold: float = 0.85) -> dict | None:
    """
    Query knowledge base for a cached verdict.

    Args:
        rule_id:      e.g. "R004"
        verdict_type: "PASS", "FAIL", or "UNCLEAR" — if None checks all
        threshold:    minimum confidence to return cached result

    Returns:
        dict with verdict, evidence, confidence if found above threshold
        None if not found or confidence too low
    """
    init_kb()

    files_to_check = (
        {verdict_type: VERDICT_FILE_MAP[verdict_type]}
        if verdict_type and verdict_type in VERDICT_FILE_MAP
        else VERDICT_FILE_MAP
    )

    for v_type, filepath in files_to_check.items():
        if not filepath.exists():
            continue

        content  = filepath.read_text(encoding="utf-8")
        existing = _parse_existing_entry(content, rule_id)

        if existing and existing["confidence"] >= threshold:
            # Extract evidence from block
            evidence_match = re.search(
                r"\*\*Evidence:\*\* (.+?)(?=\n-|\n\n)", 
                existing["block"], re.DOTALL
            )
            evidence = evidence_match.group(1).strip() if evidence_match else ""

            return {
                "verdict":    v_type,
                "evidence":   evidence,
                "confidence": existing["confidence"],
                "times_seen": existing["times_seen"],
                "source":     "knowledge_base"
            }

    return None


def get_kb_summary() -> dict:
    """Returns a summary of what is in the knowledge base."""
    init_kb()

    summary = {}
    for verdict_type, filepath in VERDICT_FILE_MAP.items():
        if not filepath.exists():
            summary[verdict_type] = 0
            continue

        content = filepath.read_text(encoding="utf-8")
        count   = len(re.findall(r"^## R\d+", content, re.MULTILINE))
        summary[verdict_type] = count

    return summary


def print_kb_summary():
    """Prints a human readable knowledge base summary."""
    summary = get_kb_summary()
    total   = sum(summary.values())

    print("\n📚 Knowledge Base Summary")
    print("=" * 35)
    print(f"  ✅ PASS    : {summary.get('PASS', 0)} rules")
    print(f"  ❌ FAIL    : {summary.get('FAIL', 0)} rules")
    print(f"  ⚠️  UNCLEAR : {summary.get('UNCLEAR', 0)} rules")
    print(f"  Total     : {total} rules stored")
    print("=" * 35)