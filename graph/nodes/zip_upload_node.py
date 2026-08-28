import os
import zipfile
import io
import shutil
from typing import Dict, Any
from graph.state_schema import GraphState


# ── Canonical document tag classifier (mirrors api.py classify_file) ──────────
_NOT_FC = ("structural", "mount", "headframe", "foundation", "cert",
           "pole", "as built", "asbuilt", "sdv", "rfnsa", "rfsna")

def _classify_file(name: str) -> str:
    """
    Classify a filename into one of the CANONICAL_DOC_TAGS.
    Mirrors the classify_file() logic in api.py so both paths produce
    identical tag assignments.
    """
    ln = name.lower().replace("_", " ").replace("-", " ")
    ext = "." + ln.rsplit(".", 1)[-1] if "." in ln else ""

    # Skip non-document file types
    if ext in (".dwg", ".mp4", ".lrf", ".srt", ".mov", ".zip"):
        return "Unknown"

    # FC Drawing
    is_fc = (
        "dfc" in ln
        or "for construction" in ln
        or (" fc " in f" {ln} " and not any(x in ln for x in _NOT_FC))
        or (ln.endswith("fc.pdf") and not any(x in ln for x in _NOT_FC))
    )
    if is_fc and ext == ".pdf":
        return "FC_Drawing"

    # Structural / mount certs
    if "mount" in ln and ("cert" in ln or "structural" in ln):
        return "Mount_Certificate"
    if "headframe" in ln:
        return "Mount_Certificate"
    if "pole" in ln and "cert" in ln:
        return "Pole_Certificate"
    if "foundation" in ln and ("cert" in ln or "report" in ln):
        return "Structural_Certificate"
    if "structural" in ln and "cert" in ln:
        return "Structural_Certificate"
    if "structural" in ln:
        return "Structural_Drawings"
    if "cert" in ln:
        return "Structural_Certificate"

    # Site identity
    if "rfnsa" in ln or "rfsna" in ln or "radsite" in ln:
        return "RFNSA"

    # SDV / Site photos
    _PHOTO_KEYWORDS = ("sdv", "site photo", "dji", "img", "photo", "drone")
    is_image_ext = ext in (".jpg", ".jpeg", ".png", ".heic")
    is_timestamped = len(name.split(".")[0].replace("_", "")) >= 8 and name[0].isdigit()
    if is_image_ext and (any(k in ln for k in _PHOTO_KEYWORDS) or is_timestamped):
        return "SDV_Photos"

    # As-Built
    if "as built" in ln or "asbuilt" in ln or " ab " in ln:
        return "As-built"

    # Feasibility Report
    if "feasibility" in ln or ln.startswith("fr ") or " fr " in f" {ln} " or ln.endswith(" fr.pdf"):
        return "FR"

    # RLM
    if "rlm" in ln or "radio link" in ln:
        return "RLM"

    # DPD
    if "dpd" in ln:
        return "DPD"

    # Form A / B
    if "form ab" in ln or "formab" in ln:
        return "Form_A"
    if "form b" in ln or "formb" in ln:
        return "Form_B"
    if "form a" in ln or ("form" in ln and " a" in ln):
        return "Form_A"

    # Power docs
    if "pva" in ln or "power viability" in ln:
        return "PVA"
    if "pdt" in ln:
        return "PDT"

    # OSD
    if "osd" in ln:
        return "OSD_171"

    # Google Maps
    if "google" in ln or "maps" in ln:
        return "Google_Maps"

    # Lease Plan
    if "lease" in ln:
        return "Lease_Plan"

    return "Unknown"


def zip_upload_node(state: GraphState) -> Dict[str, Any]:
    """
    Node: ZIP Upload
    Replaces the SharePoint fetch node.  Reads a ZIP archive that has already
    been saved to disk (zip_path in state) OR falls back to direct file paths
    when running in local-dev mode (pdf_path already set).

    Responsibilities:
    - Extract all files from the ZIP into a job-scoped directory.
    - Classify each file into a canonical document tag.
    - Identify FC Drawing candidates.
    - Populate `reference_mapping` and `fc_candidates` in state.
    - If only one FC candidate exists, set `pdf_path` automatically.
    """
    job_id   = state.get("job_id", "unknown")
    zip_path = state.get("zip_path", "")
    pdf_path = state.get("pdf_path", "")

    print(f"[zip_upload] Starting for job {job_id}")

    # ── Local-dev passthrough: pdf_path already provided, nothing to unpack ──
    if not zip_path:
        if pdf_path and os.path.exists(pdf_path):
            print("[zip_upload] No ZIP provided — local-dev passthrough mode.")
            return {
                "status":            "zip_processed",
                "fc_candidates":     [os.path.basename(pdf_path)],
                "reference_mapping": state.get("reference_mapping", {}),
            }
        return {
            "status": "failed",
            "error":  "[zip_upload] Neither zip_path nor pdf_path provided.",
        }

    if not os.path.exists(zip_path):
        return {
            "status": "failed",
            "error":  f"[zip_upload] ZIP file not found at: {zip_path}",
        }

    # ── Extract ZIP into a job-scoped refs directory ──────────────────────────
    refs_dir = os.path.join("jobs", f"{job_id}_refs")
    os.makedirs(refs_dir, exist_ok=True)

    fc_candidates: list[str]              = []
    ref_mapping:   dict[str, list[str]]   = {}
    identified_as: dict[str, str]         = {}

    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            for zinfo in z.infolist():
                # Skip directories and macOS metadata artefacts
                if zinfo.is_dir():
                    continue
                raw_name = zinfo.filename
                if raw_name.startswith("__MACOSX/") or os.path.basename(raw_name).startswith("."):
                    continue

                base_name = os.path.basename(raw_name)
                if not base_name:
                    continue

                # Sanitize filename (no quotes, no ampersands, safe chars only)
                safe_name = "".join(
                    c if (c.isalnum() or c in ".-_") else "_"
                    for c in base_name
                )

                dest_path = os.path.join(refs_dir, safe_name)
                with z.open(zinfo) as src, open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

                tag = _classify_file(safe_name)
                identified_as[safe_name] = tag

                if tag == "FC_Drawing":
                    fc_candidates.append(safe_name)

                if tag != "Unknown":
                    ref_mapping.setdefault(tag, []).append(dest_path)

    except zipfile.BadZipFile as e:
        return {"status": "failed", "error": f"[zip_upload] Bad ZIP file: {e}"}
    except Exception as e:
        return {"status": "failed", "error": f"[zip_upload] Extraction error: {e}"}

    print(f"[zip_upload] Extracted {len(identified_as)} files. FC candidates: {fc_candidates}")

    if not fc_candidates:
        return {
            "status":       "failed",
            "error":        "[zip_upload] No FC Drawing found in ZIP.",
            "tip":          "Ensure at least one file has 'FC', 'DFC', or 'For Construction' in its name.",
            "files_seen":   list(identified_as.keys()),
        }

    # ── Build flat reference_mapping (str -> str | list[str]) ─────────────────
    # We merge with any existing reference_mapping already in state
    flat_ref_mapping: dict[str, Any] = state.get("reference_mapping", {}).copy()
    
    for tag, paths in ref_mapping.items():
        if len(paths) == 1:
            flat_ref_mapping[tag] = paths[0]
        else:
            flat_ref_mapping[tag] = paths

    # ── Auto-select primary FC Drawing ────────────────────────────────────────
    resolved_pdf_path = pdf_path  # preserve if already set
    if len(fc_candidates) >= 1:
        # If there are multiple, we just take the first one instead of failing
        primary_candidate = fc_candidates[0]
        candidate_path = os.path.join(refs_dir, primary_candidate)
        master_path    = os.path.join("jobs", f"{job_id}_fc.pdf")
        shutil.copy(candidate_path, master_path)
        resolved_pdf_path = master_path
        print(f"[zip_upload] Auto-selected FC Drawing: {primary_candidate} (out of {len(fc_candidates)} found)")

    return {
        "status":            "zip_processed",
        "pdf_path":          resolved_pdf_path,
        "fc_candidates":     fc_candidates,
        "reference_mapping": flat_ref_mapping,
        "metadata": {
            **state.get("metadata", {}),
            "zip_classifications": identified_as,
            "zip_path":            zip_path,
        },
    }
