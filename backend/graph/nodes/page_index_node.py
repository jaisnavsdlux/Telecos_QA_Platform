"""
page_index_node.py
──────────────────
PageIndex RAG Node — runs immediately after zip_upload.

Strategy (Free-Tier Friendly):
  • We make ONE Groq/Llama call per DOCUMENT (not per rule).
    With ~5 documents in a typical ZIP, that is 5 calls total.
  • Each call sends ALL pages of that document as images and asks
    the model to produce a structured JSON index once.
  • The resulting `page_index` is stored in GraphState and consumed
    by all downstream nodes — zero additional LLM calls for indexing.

Free-Tier limits (Llama 4 Scout on Groq):
  30 RPM / 1,000 RPD / 30,000 TPM / 500,000 TPD
  We use a 3-second gap between calls and cap at 4 images per request
  (well under the 5-image hard limit) to stay safe.
"""

import os
import time
import json
import base64
import fitz                # PyMuPDF
from typing import Dict, Any, List

import requests

from graph.state_schema import GraphState

# ── Groq / Llama 4 Scout config ──────────────────────────────────────────────
GROQ_MODEL          = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_API_URL        = "https://api.groq.com/openai/v1/chat/completions"
MAX_IMAGES_PER_CALL = 4      # Groq hard limit is 5; stay at 4 for safety
MAX_TOKENS          = 2048   # enough for a structured JSON page summary
MAX_RETRIES         = 3      # retries on 429 rate-limit errors

# Adaptive call gap: scales up when there are more docs to index.
# Base is 3 s; add 1 s per document beyond the first 3.
# This keeps us well inside the 30 RPM / 30,000 TPM free-tier limits.
BASE_CALL_GAP_SECONDS = 3.0

# FC Drawing sheet labels (0-indexed page positions)
FC_PAGE_MAP: Dict[str, List[int]] = {
    "Cover": [0], "G1": [1], "G2": [2, 3], "G3": [4],
    "G3-1": [5],  "G4": [6], "A1": [7],   "A2": [8],
    "P1":   [9],  "asset": [10], "F1": [11], "S1": [12],
    "S2":   [13], "E1": [14],
}

# Documents NOT worth visually indexing (binary / non-text assets)
SKIP_DOC_TAGS = {"Unknown", "Google_Maps", "SDV_Photos"}

# Priority order for indexing (lighter docs first, FC Drawing last)
INDEXABLE_PRIORITY = ["RLM", "FR", "As-built", "RFNSA",
                       "PVA", "DPD", "Form_A", "Form_B",
                       "Structural_Certificate", "Structural_Drawings",
                       "Mount_Certificate", "Pole_Certificate",
                       "RFNSA", "OSD_171", "Lease_Plan", "FC_Drawing"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_text_fallback(text: str, doc_tag: str = "Unknown", label: str = "Unknown") -> dict:
    """Production-grade telecom drawing field extractor with semantic guardrails.

    Strict extraction rules:
      • site_id   → ONLY H\\d{4,} pattern. No fallback. Null if not found.
      • drawing_no → H\\d{4,5}-<sheet> from title block.
      • drawing_title → whitelist-only from title block; normalized
                        (newlines/spaces collapsed).
      • doc_tag   → suppresses titles for non-drawing docs (FR, PVA, etc.)
      • coordinates → targeted extraction for RFNSA (Easting/Northing).
    """
    import re
    if not text or not text.strip():
        return {}

    summary: dict = {}
    upper = text.upper()
    lower = text.lower()

    # ── ENTITY PRE-CLASSIFICATION ─────────────────────────────────────────
    # Define entity patterns BEFORE any extraction so we never mix them up.

    # Antenna model tokens — must NEVER be used as site_id
    # Clean newlines and extra whitespace immediately
    ANTENNA_PATTERN = re.compile(
        r'\b((?:AIR|AAIU|RRU|RRH|BBU|AAU|TMA|LNA|RRUS|RRUW)\s?[\d]{2,6}[A-Z0-9]*)\b',
        re.I
    )
    antenna_tokens = set(
        m.group(0).upper().replace("\n", "").replace("\r", "").strip() 
        for m in ANTENNA_PATTERN.finditer(text)
    )

    # ── 1. Drawing Number (H\d{4,5}-<sheet>) ─────────────────────────────
    #    This IS the authoritative source — trust it over section labels.
    drawing_no_matches = re.findall(r'\b(H\d{4,5}[-–][A-Z0-9]{1,4})\b', text, re.I)
    if drawing_no_matches:
        normalized_nos = [d.upper().replace("–", "-") for d in drawing_no_matches]
        # Prefer Hxxxx-G1 style (letter+digit suffix) over plain Hxxxx-01
        with_sheet = [d for d in normalized_nos if re.search(r'-[A-Z]\d+$', d)]
        summary["drawing_no"] = (with_sheet or normalized_nos)[0]

    # ── 2. Site ID — STRICT: H\d{4,} ONLY. No fallback. ─────────────────
    #    Extract the H-number prefix from drawing_no first (most reliable).
    #    Then scan raw text. NEVER use antenna tokens or vendor names.
    site_id_found = None

    # Primary: derive from drawing_no (most reliable source)
    if summary.get("drawing_no"):
        m = re.match(r'^(H\d{4,5})', summary["drawing_no"])
        if m:
            site_id_found = m.group(1)

    # Secondary: scan text for standalone H-number
    if not site_id_found:
        for m in re.finditer(r'\b(H\d{4,5})\b', text, re.I):
            candidate = m.group(1).upper()
            # Reject if it's part of an antenna token (e.g. H in AAIU_H3)
            if not any(candidate in tok for tok in antenna_tokens):
                site_id_found = candidate
                break

    # ── 5. Audit Timeline (Issue: When was it completed?) ────────────
    # Next-Line Link for Dates
    lines = upper.split('\n')
    date_patterns = [r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', r'\b\d{1,2}-(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)-\d{2,4}\b']
    for i, line in enumerate(lines):
        if any(k in line for k in ["DATE COMPLETED", "ISSUE DATE", "DATE OF INSPECTION", "COMPLETION DATE"]):
            if i + 1 < len(lines):
                for pat in date_patterns:
                    date_match = re.search(pat, lines[i+1])
                    if date_match:
                        summary["completion_date"] = date_match.group(0)
                        break
                if "completion_date" in summary: break

    # Generic Date Scan (fallback)
    if "completion_date" not in summary:
        all_dates = []
        for pat in date_patterns:
            all_dates.extend(re.findall(pat, upper))
        if all_dates:
            summary["dates"] = sorted(list(set(all_dates)))

    summary["site_id"]        = site_id_found     # None if not found — DO NOT GUESS
    summary["site_id_confidence"] = "HIGH" if site_id_found else "LOW"

    # ── 3. Antenna Models (hard-separated from site_id) ──────────────────
    if antenna_tokens:
        summary["antenna_models"] = sorted(antenna_tokens)

    # ── 4. Audit / Inspection Personnel (Issue: Who performed it?) ────────
    lines = upper.split('\n')
    personnel_matches = []
    owner_matches = []
    
    for i, line in enumerate(lines):
        # A. Next-Line Link (Forms)
        if any(k in line for k in ["PERFORMED BY", "COMPANY NAME", "DOCUMENT AUTHOR", "REPRESENTATIVE"]):
            if i + 1 < len(lines):
                val = lines[i+1].strip()
                if len(val) > 2: personnel_matches.append(val)
        
        # Site Owner Link
        if "SITE OWNER" in line or "CLIENT" in line:
            if i + 1 < len(lines):
                val = lines[i+1].strip()
                if len(val) > 2: owner_matches.append(val)
        
        # B. Inline Match (Title Blocks)
        inline = re.findall(r'\b(?:DRN|CHK|APP|SIGNED BY)[:\s]+([A-Z\s\.]{3,25})', line)
        personnel_matches.extend(inline)

    if personnel_matches:
        # Noise Filter: Remove common boilerplate found in telecom docs
        blacklist = ["SHALL PROVIDE", "PHOTOS OF", "SITE OWNER", "CONTRACT", "AUSTINS FERRY", "PROJECT", "SCOPE", "REVISION", "DESCRIPTION", "NAME", "LICENSE", "CONTRACTOR", "PERFORMED BY", "INSPECTION", "COMPANY NAME", "DOCUMENT AUTHOR"]
        clean_people = []
        for p in personnel_matches:
            name = p.strip().upper()
            if len(name) < 3 or len(name) > 40: continue
            if any(b == name for b in blacklist): continue # Exact match blacklist
            if any(b in name for b in ["SHALL PROVIDE", "PHOTOS OF"]): continue
            
            # Strip trailing punctuation
            name = re.sub(r'[,;\.\s]+$', '', name)
            if name not in clean_people:
                clean_people.append(name)
        
        if clean_people:
            summary["performed_by"] = clean_people

    if owner_matches:
        # Simple cleanup - ignore long sentences and common labels
        clean_owners = []
        for o in owner_matches:
            val = o.strip().upper()
            if len(val) < 3 or len(val) > 40: continue
            if any(b in val for b in ["SITE NAME", "PROJECT:", "THE STRUCTURAL", "TELECOS"]): continue
            if val not in clean_owners:
                clean_owners.append(val)
        
        if clean_owners:
            summary["site_owner"] = clean_owners[0] 

    # ── 5. Site Infrastructure (Address, Mains Supply) ──────────────
    for i, line in enumerate(lines):
        # Site Address Link
        if "SITE ADDRESS" in line or "LOCATION" in line:
            if i + 1 < len(lines):
                addr = lines[i+1].strip()
                if len(addr) > 5 and "SITE NAME" not in addr.upper():
                    summary["site_address"] = addr
        
        # Electrical / Mains Supply Details (Aggressive Vertical Link)
        if any(k in line for k in ["MAINS SUPPLY", "METER NUMBER", "CONSUMER MAINS", "M.E.N", "MSB DETAILS", "SUPPLY RATING", "SUPPLY AUTHORITY", "SERVICE MAINS", "MAINS CABLE", "POINT OF SUPPLY", "CAPACITY", "PHASES"]):
            for offset in [1, 2]:
                if i + offset < len(lines):
                    supply = lines[i+offset].strip()
                    if len(supply) > 2 and not any(k in supply.upper() for k in ["SITE NAME", "DATE", "CLIENT", "PAGE", "AS PER AS"]):
                        if "electrical_details" not in summary:
                            summary["electrical_details"] = []
                        detail = f"{line.strip()}: {supply}"
                        if detail not in summary["electrical_details"]:
                            summary["electrical_details"].append(detail)
                        break

    # ── 4. Drawing Title — whitelist + blacklist ──────────────────────────
    #    Only match known FC drawing sheet titles.
    #    Annotation / callout terms are explicitly blacklisted.

    # Terms that appear in body annotations or are company names, NOT titles
    TITLE_BLACKLIST = {
        "CABLE LADDER", "CABLE TRAY", "CABLE DUCT",
        "EXISTING", "PROPOSED", "INSTALL", "REMOVE",
        "SEE DETAIL", "SEE DRAWING", "NOT TO SCALE",
        "SECTION", "DETAIL", "ELEVATION",
        "HUAWEI TECHNOLOGIES", "OPTUS", "ERICSSON", "NOKIA", "TELSTRA",
        "VODAFONE", "TPG", "HUAWEI", "LAND SURVEYORS",
    }

    # Ordered from most specific to least specific
    KNOWN_TITLES = [
        "SITE LAYOUT AND SETOUT PLAN",
        "SITE SPECIFICATIONS",
        "OVERALL SITE PLAN",
        "ANTENNA LAYOUT PLAN",
        "ANTENNA DETAIL PLAN",
        "EQUIPMENT SHELTER LAYOUT PLAN",
        "SHELTER LAYOUT PLAN",
        "EQUIPMENT SHELTER ELEVATION",
        "RF PLUMBING DIAGRAM",
        "RF PLUMBING PLAN",
        "SITE ELEVATION",
        "POWER LAYOUT PLAN",
        "ELECTRICAL LAYOUT PLAN",
        "GENERAL NOTES",
        "COVER SHEET",
        "SITE PLAN",
    ]

    # Semantic rejection patterns for "garbage" titles (Issue 1)
    REJECT_TITLE_PATTERNS = {"PTY LTD", "ABN", "ACN", "LIMITED", "INC."}
    # Required semantic keywords for drawing titles
    REQUIRED_KEYWORDS = {"PLAN", "LAYOUT", "ELEVATION", "DIAGRAM", "SPECIFICATION", "NOTES", "SHEET", "DETAIL"}

    # ONLY extract drawing titles for specific document types
    DRAWING_DOC_TYPES = {"FC_Drawing", "As-built", "RLM", "Structural_Drawings"}
    
    if doc_tag in DRAWING_DOC_TYPES:
        # ISSUE 4: Special handling for Cover
        if label == "Cover":
            summary["drawing_title"] = "COVER SHEET"
            summary["site_name"] = re.sub(r'\s+', ' ', upper).strip()[:50]
        else:
            for title in KNOWN_TITLES:
                if title in upper and title not in TITLE_BLACKLIST:
                    summary["drawing_title"] = title
                    break

            # Fallback for drawing_title: look for standalone large uppercase headings
            if "drawing_title" not in summary:
                candidates = re.findall(r'\b([A-Z]{3,}(?:\s+[A-Z]{3,}){1,4})\b', upper)
                for cand in candidates:
                    if not any(black in cand for black in TITLE_BLACKLIST) and \
                       not any(rej in cand for rej in REJECT_TITLE_PATTERNS) and \
                       any(req in cand for req in REQUIRED_KEYWORDS):
                        summary["drawing_title"] = cand
                        break
        
        # Normalize and validate title
        if summary.get("drawing_title"):
            normalized = re.sub(r'\s+', ' ', summary["drawing_title"]).strip()
            # Final semantic check
            if any(rej in normalized for rej in REJECT_TITLE_PATTERNS) or \
               not any(req in normalized for req in REQUIRED_KEYWORDS):
                summary["drawing_title"] = None
            else:
                summary["drawing_title"] = normalized

        # ISSUE 1: Title Inference from drawing_no (backfill missing titles)
        if not summary.get("drawing_title") and summary.get("drawing_no"):
            dno = summary["drawing_no"]
            if "-A1" in dno: summary["drawing_title"] = "GENERAL ARRANGEMENT"
            elif "-A" in dno: summary["drawing_title"] = "RF PLUMBING DIAGRAM"
            elif "-T" in dno: summary["drawing_title"] = "TOWER DETAILS"
            elif "-S" in dno: summary["drawing_title"] = "STRUCTURAL DETAILS"
            elif "-E" in dno: summary["drawing_title"] = "SINGLE LINE DIAGRAM"
            elif "-G1" in dno: summary["drawing_title"] = "SITE SPECIFICATIONS"
            elif "-G2" in dno: summary["drawing_title"] = "OVERALL SITE PLAN"
            elif "-G" in dno:  summary["drawing_title"] = "SITE PLAN / LAYOUT"
            
            if summary.get("drawing_title"):
                summary["title_status"] = "INFERRED"
    else:
        summary["drawing_title"] = None


    # ── 5. Drawing Status — raw + normalized ─────────────────────────────
    #    Store both so rules can match either form.
    STATUS_MAP = {
        "ISSUED FOR CONSTRUCTION": "FOR_CONSTRUCTION",
        "FOR CONSTRUCTION":        "FOR_CONSTRUCTION",
        "AS-BUILT":                "AS_BUILT",
        "AS BUILT":                "AS_BUILT",
        "FOR APPROVAL":            "FOR_APPROVAL",
        "FOR REVIEW":              "FOR_REVIEW",
        "PRELIMINARY":             "PRELIMINARY",
        "APPROVED":                "APPROVED",
        "DRAFT":                   "DRAFT",
    }
    for raw_phrase, normalized_code in STATUS_MAP.items():
        if raw_phrase in upper:
            summary["raw_status"]        = raw_phrase
            summary["normalized_status"] = normalized_code
            break

    # ── 6. Revision ──────────────────────────────────────────────────────
    rev = re.search(
        r'(?:REV(?:ISION)?|AMENDMENT|AMD)[\s.:=-]*([A-Z0-9]{1,3})\b', text, re.I
    )
    if not rev:
        rev = re.search(r'\bRev\.?\s+([A-Z]{1,2})\b', text)
    if rev:
        summary["revision"] = rev.group(1).upper()

    # ── 7. WA / Job Number ───────────────────────────────────────────────
    wa = re.search(r'\b(WA[-\s]?\d{5,8})\b', text, re.I)
    if wa:
        summary["wa_number"] = wa.group(0).strip().upper()
    else:
        job = re.search(r'\b(\d{6})\b', text)
        if job:
            # Must not be the same digits as a known site_id-style number
            summary["wa_number"] = job.group(0)

    # ── 8. Dates ─────────────────────────────────────────────────────────
    dates = re.findall(
        r'\b(\d{2}[/.-]\d{2}[/.-]\d{4}|\d{2}-[A-Za-z]{3}-\d{2,4}|\d{4}-\d{2}-\d{2})\b',
        text
    )
    if dates:
        summary["dates"] = list(dict.fromkeys(dates))[:5]

    # ── 9. Coordinates (targeted for RFNSA / R029) ───────────────────────
    # Look for Lat/Lon
    lat_lon = re.findall(r'(-?\d{1,3}\.\d{4,})', text)
    if len(lat_lon) >= 2:
        summary["coordinates"] = {"lat": lat_lon[0], "lon": lat_lon[1]}

    # Targeted Easting/Northing/Zone for RFNSA
    if "RFNSA" in doc_tag or "coordinate" in lower:
        easting = re.search(r'Easting[:\s]+(\d{6,7})', text, re.I)
        northing = re.search(r'Northing[:\s]+(\d{7})', text, re.I)
        zone = re.search(r'Zone[:\s]+(\d{2})', text, re.I)
        if easting or northing:
            summary["rf_location"] = {
                "easting": easting.group(1) if easting else None,
                "northing": northing.group(1) if northing else None,
                "zone": zone.group(1) if zone else None
            }

    # ── 3. Engineering Metadata (Scale, Azimuths, etc.) ──────────────
    # Scale detection (e.g. 1:100, 1:50, AS SHOWN)
    scale_match = re.search(r'\bSCALE[:\s]+(\d+:\d+|AS SHOWN|NTS|1\.\d+)\b', upper)
    if scale_match:
        summary["scale"] = scale_match.group(1)

    # ── 10. Azimuths ─────────────────────────────────────────────────────
    azimuths = re.findall(r'\b(\d{1,3})\s?(?:°|deg)\b', text, re.I)
    if azimuths:
        summary["azimuths"] = sorted(set(azimuths), key=int)

    return summary


def _pdf_page_to_b64(doc: fitz.Document, page_idx: int, dpi: int = 100) -> str:
    """Render a single PDF page to a base64 PNG string.

    DPI is intentionally kept LOW (100) to minimise token count.
    Engineering drawings are large but the key data (labels, values)
    remain legible at this resolution.
    """
    if page_idx >= len(doc):
        return ""
    pix  = doc[page_idx].get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))
    return base64.b64encode(pix.tobytes("png")).decode()


def _adaptive_call_gap(total_docs: int) -> float:
    """Return a call gap (seconds) that scales with the number of documents.

    Formula: BASE + 1 s per doc beyond the first 3.
    Examples:
      3 docs  → 3.0 s gap
      6 docs  → 6.0 s gap
      10 docs → 10.0 s gap
    This ensures we never exceed 20 RPM even on large ZIPs.
    """
    return BASE_CALL_GAP_SECONDS + max(0, total_docs - 3) * 1.0


def _call_groq_vision(
    images_b64: List[str],
    system_prompt: str,
    user_prompt: str,
    call_gap: float,
    page_count: int = 1,
) -> dict:
    """Send a multimodal request to Groq and return the parsed JSON response.

    Args:
        call_gap:   seconds to sleep AFTER a successful call (adaptive).
        page_count: number of pages in this batch — used to scale HTTP timeout.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("[page_index] GROQ_API_KEY not set in environment.")

    # Scale HTTP timeout: 30 s base + 15 s per page in the batch.
    # A 4-page batch with large drawings can take ~90 s on Groq's free tier.
    http_timeout = 30 + (page_count * 15)

    content: List[dict] = [{"type": "text", "text": user_prompt}]
    for b64 in images_b64[:MAX_IMAGES_PER_CALL]:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}"}
        })

    payload = {
        "model":   GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": content},
        ],
        "max_completion_tokens": MAX_TOKENS,
        "temperature":           0,
        "response_format":       {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
    }

    # Retry loop with exponential backoff for 429 rate-limit errors
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                GROQ_API_URL, headers=headers, json=payload, timeout=http_timeout
            )
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("retry-after", call_gap * attempt))
                print(f"[page_index] Rate limited (429). Waiting {retry_after}s "
                      f"before retry {attempt}/{MAX_RETRIES}...")
                time.sleep(retry_after)
                continue

            resp.raise_for_status()
            raw_text = resp.json()["choices"][0]["message"]["content"]
            
            # Clean markdown JSON block formatting if present
            cleaned_text = raw_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            
            try:
                result = json.loads(cleaned_text)
            except json.JSONDecodeError as jde:
                print(f"[page_index] JSON Parse Error: {jde}\nRAW TEXT:\n{raw_text}")
                result = {}
                
            # Adaptive gap AFTER a successful call
            time.sleep(call_gap)
            return result

        except requests.exceptions.Timeout:
            wait = call_gap * attempt
            print(f"[page_index] Timeout on attempt {attempt}/{MAX_RETRIES}. "
                  f"Retrying in {wait}s...")
            time.sleep(wait)

    raise RuntimeError(f"[page_index] Groq call failed after {MAX_RETRIES} attempts.")


def _index_pdf_document(
    doc_tag: str,
    file_path: str,
    call_gap: float,
) -> Dict[str, Any]:
    """
    Build the page index for a single PDF document.

    For the FC Drawing we use FC_PAGE_MAP labels.
    For reference docs (RLM, FR, …) we use Page_N labels.

    Args:
        call_gap: adaptive gap between Groq calls (seconds).
    """
    index: Dict[str, Any] = {}

    try:
        doc = fitz.open(file_path)
    except Exception as e:
        print(f"[page_index] Cannot open {file_path}: {e}")
        return index

    total_pages = len(doc)
    print(f"[page_index]   {doc_tag} has {total_pages} pages - "
          f"will need {-(-total_pages // MAX_IMAGES_PER_CALL)} Groq call(s).")

    # 1. Extract text + render images via PyMuPDF (free, instant)
    page_data: Dict[str, Dict[str, str]] = {}

    if doc_tag == "FC_Drawing":
        idx_to_label: Dict[int, str] = {}
        for label, indices in FC_PAGE_MAP.items():
            for idx in indices:
                idx_to_label[idx] = label
        for page_idx in range(total_pages):
            label = idx_to_label.get(page_idx, f"Page_{page_idx}")
            text  = doc[page_idx].get_text()
            b64   = _pdf_page_to_b64(doc, page_idx)
            page_data[label] = {"text": text, "image_b64": b64}
    else:
        # Cap reference docs at 15 pages to stay within token budget
        cap = min(total_pages, 15)
        if total_pages > 15:
            print(f"[page_index]   Capping {doc_tag} at 15 pages (has {total_pages}).")
        for page_idx in range(cap):
            label = f"Page_{page_idx}"
            text  = doc[page_idx].get_text()
            b64   = _pdf_page_to_b64(doc, page_idx)
            page_data[label] = {"text": text, "image_b64": b64}

    doc.close()

    # 2. Send pages to Groq in batches for structured extraction
    labels     = list(page_data.keys())
    all_images = [page_data[l]["image_b64"] for l in labels]
    num_batches = -(-len(labels) // MAX_IMAGES_PER_CALL)  # ceiling division

    system_prompt = (
        "You are a Telecom Engineering Drawing Analyst specializing in Australian FC drawings. "
        "For EACH page image, extract ONLY the following fields from the TITLE BLOCK "
        "(typically bottom-right strip of the sheet). "
        "Do NOT pick random text from the drawing body.\n\n"
        "Required fields:\n"
        "  drawing_no:     Drawing number (format: Hxxxx-G1, Hxxxx-A2, etc.)\n"
        "  site_id:        Site identifier (format: Hxxxx, e.g. H8097). "
        "                  This is the PREFIX of the drawing number. "
        "                  Do NOT use vendor names like HUAWEI or NOKIA.\n"
        "  drawing_title:  Full title (e.g. SITE LAYOUT AND SETOUT PLAN)\n"
        "  drawing_status: Exactly one of: FOR CONSTRUCTION, AS BUILT, DRAFT, FOR APPROVAL\n"
        "  revision:       Revision code (e.g. A, AB, 01)\n"
        "  date:           Issue date if visible\n"
        "  coordinates:    Lat/Lon if visible (decimal degrees)\n"
        "  azimuths:       List of azimuth values if visible (degrees)\n"
        "  antenna_models: Antenna model numbers if visible\n\n"
        "Return a JSON object where each key is the page label provided "
        "and each value is a dict of the above fields. "
        "Omit fields that are not visible. "
        "Example: {\"Page_0\": {\"drawing_no\": \"H8097-G3\", \"site_id\": \"H8097\", "
        "\"drawing_title\": \"SITE LAYOUT AND SETOUT PLAN\", "
        "\"drawing_status\": \"FOR CONSTRUCTION\", \"revision\": \"AB\"}}"
    )

    for batch_num, batch_start in enumerate(range(0, len(labels), MAX_IMAGES_PER_CALL), 1):
        batch_labels = labels[batch_start: batch_start + MAX_IMAGES_PER_CALL]
        batch_images = all_images[batch_start: batch_start + MAX_IMAGES_PER_CALL]

        label_list  = ", ".join(batch_labels)
        user_prompt = (
            f"These are pages labeled: {label_list}. "
            "Extract the title block fields for each page. "
            "IMPORTANT: site_id must be the Hxxxx code, NOT a vendor name. "
            "Return JSON as instructed."
        )

        print(f"[page_index]   Batch {batch_num}/{num_batches} -> pages: {batch_labels} "
              f"(gap={call_gap:.1f}s)")
        try:
            result = _call_groq_vision(
                batch_images, system_prompt, user_prompt,
                call_gap=call_gap,
                page_count=len(batch_images),
            )
            # DEBUG: print the actual keys Groq returned so we can see what's happening
            print(f"[page_index]   Groq returned keys: {list(result.keys())[:10]}")

            # Robust recursive search for the page label in the JSON
            def _find_key_recursive(d, target_key):
                if not isinstance(d, dict): return None
                for k, v in d.items():
                    if str(k).lower() == target_key.lower() and isinstance(v, dict):
                        return v
                for k, v in d.items():
                    if isinstance(v, dict):
                        res = _find_key_recursive(v, target_key)
                        if res: return res
                return None
            
            for label in batch_labels:
                found_data = _find_key_recursive(result, label)
                if found_data:
                    page_data[label]["summary"] = found_data
                else:
                    # FALLBACK: extract key values from the raw PyMuPDF text
                    page_data[label]["summary"] = _parse_text_fallback(page_data[label].get("text", ""), doc_tag, label)


        except Exception as e:
            print(f"[page_index]   x Groq call failed for {doc_tag}/{batch_labels}: {e} - using text fallback.")
            for label in batch_labels:
                page_data[label]["summary"] = _parse_text_fallback(page_data[label].get("text", ""), doc_tag, label)

    # Build final index as a Semantic Tree Structure
    master_tree = {
        "title": f"Document: {doc_tag}",
        "node_id": doc_tag,
        "start_index": 0,
        "end_index": len(labels) - 1,
        "summary": f"Telecom Engineering Document ({total_pages} pages)",
        "nodes": []
    }

    for i, (label, data) in enumerate(page_data.items()):
        # Build leaf node for each page
        summary_dict = data.get("summary", {})
        page_title = f"Section: {label}"
        if summary_dict.get("drawing_status"):
            page_title += f" ({summary_dict['drawing_status']})"
        elif summary_dict.get("revision"):
            page_title += f" (Rev {summary_dict['revision']})"

        # Create the page-level node mimicking PageIndex structure
        page_node = {
            "title": page_title,
            "node_id": f"{doc_tag}_{label}",
            "start_index": i,
            "end_index": i,
            "summary": summary_dict.get("notes", f"Extracted engineering parameters for {label}"),
            "extracted_fields": summary_dict,
            "text": data.get("text", "")
        }
        master_tree["nodes"].append(page_node)
        
        # Keep backward compatibility for images
        index[label] = {
            "summary": summary_dict,
            "text": data.get("text", "")
        }

    index["tree"] = master_tree
    return index


def _enrich_page_index(page_index: Dict[str, Any]) -> Dict[str, Any]:
    """
    PageIndex v1.2 - Audit Readiness Layer (Aggregation & Classification).
    """
    import re
    from collections import defaultdict

    # 1. Global Context Collection
    global_site_id = None
    global_coords = None
    coord_priority = ["RFNSA", "Mount_Certificate", "Pole_Certificate", "FC_Drawing"]
    
    # Tiered WA logic (Issue 3)
    PRIMARY_DOCS = {"FC_Drawing", "RLM", "As-built"}
    
    # First pass: collect site_id and best coordinates
    for src in coord_priority:
        if src in page_index:
            for label, page in page_index[src].items():
                if label == "tree": continue
                summ = page.get("summary", {})
                if not global_site_id and summ.get("site_id_confidence") == "HIGH":
                    global_site_id = summ["site_id"]
                if not global_coords and (summ.get("coordinates") or summ.get("rf_location")):
                    global_coords = summ.get("coordinates") or summ.get("rf_location")
                    global_coords["source"] = src
                    global_coords["confidence"] = "HIGH" if src == "RFNSA" else "DERIVED"

    # 2. Document Enrichment & Aggregation
    for doc_tag, doc_data in page_index.items():
        if not isinstance(doc_data, dict): continue
        
        seen_drawing_nos = {} 
        doc_has_data = False
        
        # Aggregation buckets (Issue 2)
        doc_antenna_models = set()
        doc_wa_numbers = set()
        doc_drawing_inventory = set()
        
        for label, page in doc_data.items():
            if label == "tree": continue
            summary = page.get("summary", {})
            if not summary: continue
            doc_has_data = True

            # Aggregate models and WAs
            if summary.get("antenna_models"):
                doc_antenna_models.update(summary["antenna_models"])
            if summary.get("wa_number"):
                doc_wa_numbers.add(summary["wa_number"])

            # A. Site ID & Coordinate Propagation
            if not summary.get("site_id") or summary.get("site_id_confidence") == "LOW":
                if global_site_id:
                    summary["site_id"] = global_site_id
                    summary["site_id_source"] = "CONTEXTUAL"
                    summary["site_id_confidence"] = "DERIVED"
            
            if not summary.get("coordinates") and global_coords:
                summary["coordinates_context"] = global_coords

            # B. Duplicate Resolution
            dno = summary.get("drawing_no")
            if dno:
                doc_drawing_inventory.add(dno)
                if dno in seen_drawing_nos:
                    summary["resolution"] = "MERGED"
                    summary["primary_label"] = seen_drawing_nos[dno]
                    summary["integrity_warning"] = f"Duplicate drawing_no {dno} (also on {seen_drawing_nos[dno]})"
                else:
                    seen_drawing_nos[dno] = label
                
                # C. Resolution of Label Alignment
                suffix_match = re.search(r'-([A-Z]\d+)$', dno)
                if suffix_match:
                    suffix = suffix_match.group(1)
                    if label != suffix and label not in ["Cover", "asset"] and not label.startswith("Page_"):
                        summary["label_mismatch"] = f"Section label {label} contradicts drawing_no truth {dno}"
                        summary["resolved_section"] = suffix
                        summary["section_status"] = "CORRECTED"

        # D. Document-Level Aggregation (v1.2)
        if "tree" in doc_data:
            tree = doc_data["tree"]
            tree["aggregated_data"] = {
                "antenna_models": sorted(list(doc_antenna_models)),
                "wa_numbers": sorted(list(doc_wa_numbers)),
                "drawing_inventory": sorted(list(doc_drawing_inventory))
            }
            # WA Classification (Issue 3)
            if doc_tag in PRIMARY_DOCS:
                tree["wa_tier"] = "PRIMARY"
                tree["primary_wa"] = sorted(list(doc_wa_numbers))[0] if doc_wa_numbers else None
            else:
                tree["wa_tier"] = "SECONDARY"
                tree["secondary_was"] = sorted(list(doc_wa_numbers))

        if not doc_has_data:
            doc_data["extraction_status"] = "NO_RELEVANT_FIELDS"

    return page_index


# ── Node Entry Point ──────────────────────────────────────────────────────────

def page_index_node(state: GraphState) -> Dict[str, Any]:
    """
    Graph Node: PageIndex RAG
    """
    job_id      = state.get("job_id", "unknown")
    ref_mapping = state.get("reference_mapping", {})
    pdf_path    = state.get("pdf_path", "")

    # ── Collect all documents to index ───────────────────────────────────────
    docs_to_index: List[tuple] = []
    seen_tags = set()
    for tag in INDEXABLE_PRIORITY:
        if tag in ref_mapping and tag not in SKIP_DOC_TAGS:
            path_entry = ref_mapping[tag]
            file_path  = path_entry[0] if isinstance(path_entry, list) else path_entry
            if file_path and os.path.exists(file_path):
                docs_to_index.append((tag, file_path))
                seen_tags.add(tag)

    for tag, path_entry in ref_mapping.items():
        if tag not in seen_tags and tag not in SKIP_DOC_TAGS:
            file_path = path_entry[0] if isinstance(path_entry, list) else path_entry
            if file_path and os.path.exists(file_path):
                docs_to_index.append((tag, file_path))

    if pdf_path and os.path.exists(pdf_path) and ("FC_Drawing", pdf_path) not in docs_to_index:
        docs_to_index.append(("FC_Drawing", pdf_path))

    total_docs = len(docs_to_index)
    call_gap   = _adaptive_call_gap(total_docs)

    print(f"[page_index] Indexing {total_docs} docs...")

    # ── Index each document ───────────────────────────────────────────────────
    page_index: Dict[str, Any] = {}
    for doc_num, (doc_tag, file_path) in enumerate(docs_to_index, 1):
        try:
            doc_index = _index_pdf_document(doc_tag, file_path, call_gap)
            if doc_index:
                page_index[doc_tag] = doc_index
        except Exception as e:
            print(f"[page_index] {doc_tag} failed: {e}")

    # ── ENRICHMENT LAYER (The "Real System" Logic) ──────────────────────────
    page_index = _enrich_page_index(page_index)

    print(f"[page_index] Complete - {len(page_index)} docs indexed.")

    return {
        "page_index": page_index,
        "status":     "page_indexed",
        "metadata": {
            **state.get("metadata", {}),
            "page_index_stats": {
                "docs_indexed": len(page_index),
                "total_pages": sum(len(d)-1 for d in page_index.values() if isinstance(d, dict))
            }
        }
    }
