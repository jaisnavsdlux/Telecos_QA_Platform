"""
Project & Engineering Workspace Service.
Manages isolated multi-project directories, CAD drawing ingestion,
title-block sheet index parsing, companion reference classification,
project updates, and deletion.
"""
import os
import re
import io
import json
import shutil
import zipfile
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
import fitz  # PyMuPDF

from backend.config import PROJECTS_DIR, REFERENCE_FILES_DIR, BASE_DIR

_PROJECT_LOCK = threading.RLock()
LEGACY_PROJECTS_DIR = os.path.join(BASE_DIR, "projects")

def classify_file(name: str) -> str:
    """
    Classify an uploaded companion file by its filename into canonical telecom doc tags.
    """
    ln = name.lower().replace("_", " ").replace("-", " ")
    ext = "." + ln.rsplit(".", 1)[-1] if "." in ln else ""

    if ext in (".dwg", ".mp4", ".lrf", ".srt", ".mov", ".zip"):
        return "Unknown"

    _NOT_FC = ("structural", "mount", "headframe", "foundation", "cert",
               "pole", "as built", "asbuilt", "sdv", "rfnsa", "rfsna")

    is_fc_keyword = (
        "dfc" in ln
        or "for construction" in ln
        or (" fc " in f" {ln} " and not any(x in ln for x in _NOT_FC))
        or (ln.endswith("fc.pdf") and not any(x in ln for x in _NOT_FC))
    )
    if is_fc_keyword and ext == ".pdf":
        return "FC_Drawing"

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

    if "rfnsa" in ln or "rfsna" in ln or "radsite" in ln:
        return "RFNSA"

    _PHOTO_KEYWORDS = ("sdv", "site photo", "dji", "img", "photo", "drone")
    is_image_ext = ext in (".jpg", ".jpeg", ".png", ".heic")
    is_timestamped = len(name.split(".")[0].replace("_", "")) >= 8 and name[0].isdigit()
    if is_image_ext and (any(k in ln for k in _PHOTO_KEYWORDS) or is_timestamped):
        return "SDV_Photos"

    if "as built" in ln or "asbuilt" in ln or " ab " in ln:
        return "As-built"
    if "feasibility" in ln or ln.startswith("fr ") or " fr " in f" {ln} " or ln.endswith(" fr.pdf"):
        return "FR"
    if "rlm" in ln or "radio link" in ln or ("phase" in ln and "rlm" in ln):
        return "RLM"
    if "dpd" in ln or ("detail" in ln and "plumb" in ln):
        return "DPD"
    if "sp1" in ln or "sc184419" in ln:
        return "SP1_Certificate"
    if "lease" in ln or "tenancy" in ln or "cadastral" in ln:
        return "Lease_Plan"
    if "air3268" in ln or "rrvv" in ln or "avql" in ln or "product description" in ln or "antenna spec" in ln:
        return "Equipment_Specs"
    if "form ab" in ln or "formab" in ln:
        return "Form_A"
    if "form b" in ln or "formb" in ln:
        return "Form_B"
    if "form a" in ln or "forma" in ln:
        return "Form_A"
    if "osd" in ln:
        return "OSD"
    if "pdt" in ln or "power design" in ln:
        return "PDT"
    if "pva" in ln:
        return "PVA"
    if "checklist" in ln:
        return "Checklist"
    if "environmental" in ln or "heritage" in ln:
        return "Environmental"
    if "geotech" in ln or "soil" in ln:
        return "Geotech"
    if "survey" in ln:
        return "Survey"

    return "General_Companion"


class ProjectService:
    @staticmethod
    def get_project_dir(project_id: str = "H8097") -> str:
        """Returns the canonical absolute directory for a project workspace and ensures subdirs exist."""
        pid = re.sub(r'[^a-zA-Z0-9_-]', '', (project_id or "H8097").upper().strip()) or "H8097"
        pdir = os.path.join(PROJECTS_DIR, pid)
        legacy_pdir = os.path.join(LEGACY_PROJECTS_DIR, pid)
        
        with _PROJECT_LOCK:
            os.makedirs(os.path.join(pdir, "drawing"), exist_ok=True)
            os.makedirs(os.path.join(pdir, "references"), exist_ok=True)
            os.makedirs(os.path.join(pdir, "reports"), exist_ok=True)

            os.makedirs(os.path.join(legacy_pdir, "drawing"), exist_ok=True)
            os.makedirs(os.path.join(legacy_pdir, "references"), exist_ok=True)
            os.makedirs(os.path.join(legacy_pdir, "reports"), exist_ok=True)

            # Auto-seed baseline files for H8097 from qaInput on every boot
            if pid == "H8097":
                qa_ref_dir = os.path.join(BASE_DIR, "qaInput", "reference_package")
                if os.path.exists(qa_ref_dir):
                    for dst_ref_dir in [os.path.join(pdir, "references"), os.path.join(legacy_pdir, "references")]:
                        os.makedirs(dst_ref_dir, exist_ok=True)
                        for f in os.listdir(qa_ref_dir):
                            src_f = os.path.join(qa_ref_dir, f)
                            dst_f = os.path.join(dst_ref_dir, f)
                            if os.path.isfile(src_f):
                                try:
                                    shutil.copy2(src_f, dst_f)
                                except Exception:
                                    pass

                qa_dwg_dir = os.path.join(BASE_DIR, "qaInput", "primary_drawing")
                if os.path.exists(qa_dwg_dir):
                    for dst_dwg_dir in [os.path.join(pdir, "drawing"), os.path.join(legacy_pdir, "drawing")]:
                        os.makedirs(dst_dwg_dir, exist_ok=True)
                        for f in os.listdir(qa_dwg_dir):
                            src_f = os.path.join(qa_dwg_dir, f)
                            dst_f = os.path.join(dst_dwg_dir, f)
                            if os.path.isfile(src_f):
                                try:
                                    shutil.copy2(src_f, dst_f)
                                except Exception:
                                    pass

                # Purge any 1-page blank stubs from drawing folder
                pdir_dwg = os.path.join(pdir, "drawing")
                if os.path.exists(pdir_dwg):
                    for f in os.listdir(pdir_dwg):
                        fp = os.path.join(pdir_dwg, f)
                        if os.path.isfile(fp) and f.lower().startswith(f"{pid.lower()}_drawing.pdf") and os.path.getsize(fp) < 50000:
                            try:
                                os.remove(fp)
                            except Exception:
                                pass

            # Check if legacy directory has files not present in db/projects
            if os.path.exists(legacy_pdir):
                for sub in ("drawing", "references", "reports"):
                    src_sub = os.path.join(legacy_pdir, sub)
                    dst_sub = os.path.join(pdir, sub)
                    if os.path.exists(src_sub):
                        for f in os.listdir(src_sub):
                            src_file = os.path.join(src_sub, f)
                            dst_file = os.path.join(dst_sub, f)
                            if os.path.isfile(src_file) and not os.path.exists(dst_file):
                                try:
                                    shutil.copy2(src_file, dst_file)
                                except Exception:
                                    pass

        return pdir

    @staticmethod
    def get_project_meta(project_id: str = "H8097") -> Dict[str, Any]:
        """Loads metadata for a specific project workspace with auto-discovery."""
        pid = re.sub(r'[^a-zA-Z0-9_-]', '', (project_id or "H8097").upper().strip()) or "H8097"
        pdir = ProjectService.get_project_dir(pid)
        meta_file = os.path.join(pdir, "project.json")

        with _PROJECT_LOCK:
            meta = None
            if os.path.exists(meta_file):
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except Exception:
                    pass

            dwg_dir = os.path.join(pdir, "drawing")
            dwg_files = [f for f in os.listdir(dwg_dir) if f.lower().endswith(('.pdf', '.dwg'))] if os.path.exists(dwg_dir) else []
            primary_dwg = dwg_files[0] if dwg_files else ("H8097_AUSTINS FERRY_FC_05122025_Final PDF After QC validation.pdf" if pid == "H8097" else "No drawing uploaded")

            if meta is None:
                meta = {
                    "id": pid,
                    "name": "AUSTINS FERRY" if pid == "H8097" else pid,
                    "code": pid,
                    "structure_type": "CONCRETE MONOPOLE (26.8m)" if pid == "H8097" else "TELECOM STRUCTURE",
                    "drawing_revision": "FOR CONSTRUCTION (Rev 1.0)",
                    "primary_drawing": primary_dwg,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "sheets": []
                }

            # If primary drawing exists in directory but metadata shows empty, update metadata
            if dwg_files and (not meta.get("primary_drawing") or meta.get("primary_drawing") == "No drawing uploaded"):
                meta["primary_drawing"] = dwg_files[0]
                # Auto parse sheets if empty
                if not meta.get("sheets"):
                    parsed = ProjectService.parse_pdf_sheets(os.path.join(dwg_dir, dwg_files[0]))
                    meta["sheets"] = [f"Sheet {s['sheet']}: {s['title']}" for s in parsed] if parsed else []
                ProjectService.save_project_meta(pid, meta)

            if pid == "H8097" and not meta.get("sheets"):
                meta["sheets"] = [
                    "Sheet Cover: Title Block & Drawing Index",
                    "Sheet G1: Site Specifications & Access",
                    "Sheet G2: Overall Site Plan",
                    "Sheet G3: Site Layout & Setout Plan",
                    "Sheet G3-1: Antenna Layout & Clearance",
                    "Sheet G4: Site Elevation",
                    "Sheet A1: Antenna Schedule (Optus & Vodafone)",
                    "Sheet A2: Antenna Configuration Detail",
                    "Sheet P1: RF Plumbing Diagram",
                    "Sheet F1: Equipment Shelter Layout Plan"
                ]

            return meta

    @staticmethod
    def save_project_meta(project_id: str, meta: Dict[str, Any]) -> None:
        """Saves metadata for a project to both db and legacy workspaces."""
        pid = re.sub(r'[^a-zA-Z0-9_-]', '', (project_id or "H8097").upper().strip()) or "H8097"
        pdir = ProjectService.get_project_dir(pid)
        legacy_pdir = os.path.join(LEGACY_PROJECTS_DIR, pid)
        
        with _PROJECT_LOCK:
            with open(os.path.join(pdir, "project.json"), "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)
            try:
                os.makedirs(legacy_pdir, exist_ok=True)
                with open(os.path.join(legacy_pdir, "project.json"), "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2)
            except Exception:
                pass

    @staticmethod
    def list_all_projects() -> List[Dict[str, Any]]:
        """Lists all projects with their latest verdicts, drawing names, and file stats."""
        projects_map = {}
        with _PROJECT_LOCK:
            # Scan both PROJECTS_DIR and LEGACY_PROJECTS_DIR
            for base_dir in (PROJECTS_DIR, LEGACY_PROJECTS_DIR):
                if os.path.exists(base_dir):
                    for pid in sorted(os.listdir(base_dir)):
                        pdir = os.path.join(base_dir, pid)
                        if os.path.isdir(pdir):
                            clean_pid = re.sub(r'[^a-zA-Z0-9_-]', '', pid.upper().strip())
                            if clean_pid and clean_pid not in projects_map:
                                meta = ProjectService.get_project_meta(clean_pid)
                                
                                # Count reference files recursively
                                ref_dir = os.path.join(pdir, "references")
                                ref_count = 0
                                if os.path.exists(ref_dir):
                                    for root, _, files in os.walk(ref_dir):
                                        ref_count += len(files)
                                
                                # Fallback for baseline H8097
                                if clean_pid == "H8097" and ref_count == 0 and os.path.exists(REFERENCE_FILES_DIR):
                                    ref_count = len(os.listdir(REFERENCE_FILES_DIR))

                                rpts_dir = os.path.join(pdir, "reports")
                                rpts = [f for f in os.listdir(rpts_dir) if f.endswith(".pdf")] if os.path.exists(rpts_dir) else []

                                latest_v = meta.get("latest_verdict")
                                if not latest_v and rpts:
                                    top_rpt = os.path.join(rpts_dir, sorted(rpts, reverse=True)[0])
                                    from backend.services.report_service import extract_pdf_verdicts
                                    pv = extract_pdf_verdicts(top_rpt)
                                    if pv.get("PASS", 0) + pv.get("FAIL", 0) + pv.get("NOT_APPLICABLE", 0) > 0:
                                        latest_v = {
                                            "pass": pv.get("PASS", 0),
                                            "fail": pv.get("FAIL", 0),
                                            "unclear": pv.get("UNCLEAR", 0),
                                            "na": pv.get("NOT_APPLICABLE", 0),
                                            "total": sum(pv.values())
                                        }
                                if not latest_v:
                                    latest_v = {"pass": 0, "fail": 0, "unclear": 0, "na": 0, "total": 0}

                                projects_map[clean_pid] = {
                                    "id": clean_pid,
                                    "name": meta.get("name", clean_pid),
                                    "code": meta.get("code", clean_pid),
                                    "structure_type": meta.get("structure_type", "Telecom Structure"),
                                    "drawing_revision": meta.get("drawing_revision", "FOR CONSTRUCTION (Rev 1.0)"),
                                    "primary_drawing": meta.get("primary_drawing", ""),
                                    "reference_files_count": ref_count,
                                    "reports_count": len(rpts),
                                    "created_at": meta.get("created_at", ""),
                                    "latest_verdict": latest_v
                                }
        return list(projects_map.values())

    @staticmethod
    def create_project(project_id: str, name: str = "", structure_type: str = "", drawing_revision: str = "") -> Dict[str, Any]:
        """Creates a new isolated project workspace."""
        pid = re.sub(r'[^a-zA-Z0-9_-]', '', project_id.upper().strip())
        if not pid:
            raise ValueError("Valid Site ID / Project ID required.")

        pdir = ProjectService.get_project_dir(pid)
        meta = {
            "id": pid,
            "name": name.strip() or pid,
            "code": pid,
            "structure_type": structure_type.strip() or "CONCRETE MONOPOLE (26.8m)",
            "drawing_revision": drawing_revision.strip() or "FOR CONSTRUCTION (Rev 1.0)",
            "primary_drawing": "",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sheets": []
        }
        ProjectService.save_project_meta(pid, meta)
        return meta

    @staticmethod
    def update_project(project_id: str, name: Optional[str] = None, structure_type: Optional[str] = None, drawing_revision: Optional[str] = None) -> Dict[str, Any]:
        """Renames/updates metadata for a project."""
        pid = re.sub(r'[^a-zA-Z0-9_-]', '', project_id.upper().strip())
        if not pid:
            raise ValueError("Valid Project ID required.")

        meta = ProjectService.get_project_meta(pid)
        if name is not None and name.strip():
            meta["name"] = name.strip()
        if structure_type is not None and structure_type.strip():
            meta["structure_type"] = structure_type.strip()
        if drawing_revision is not None and drawing_revision.strip():
            meta["drawing_revision"] = drawing_revision.strip()

        ProjectService.save_project_meta(pid, meta)
        return meta

    @staticmethod
    def delete_project(project_id: str) -> None:
        """Permanently deletes a project workspace and all its data (except baseline H8097)."""
        pid = re.sub(r'[^a-zA-Z0-9_-]', '', project_id.upper().strip())
        if pid == "H8097":
            raise ValueError("Cannot delete baseline project H8097.")

        with _PROJECT_LOCK:
            for base in (PROJECTS_DIR, LEGACY_PROJECTS_DIR):
                pdir = os.path.join(base, pid)
                if os.path.exists(pdir):
                    try:
                        shutil.rmtree(pdir)
                    except Exception as e:
                        raise RuntimeError(f"Failed to delete project directory {pdir}: {e}")

    @staticmethod
    def parse_pdf_sheets(file_path: str) -> List[Dict[str, str]]:
        """Parses a CAD drawing package PDF to discover sheet titles and numbers."""
        sheets = []
        if not os.path.exists(file_path):
            return sheets

        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()

                sheet_code = f"P{page_num + 1}"
                sheet_title = "General Arrangement"

                code_match = re.search(r'(?:SHEET|DWG|DRG|DRAWING|NO\.?)\s*[:\.]?\s*([A-Z0-9\-_]{2,10})', text, re.IGNORECASE)
                if code_match:
                    sheet_code = code_match.group(1).upper()

                title_match = re.search(r'(?:TITLE|DESCRIPTION)\s*[:\.]?\s*([A-Za-z0-9\s\-_/\&]{4,40})', text, re.IGNORECASE)
                if title_match:
                    sheet_title = title_match.group(1).strip()
                else:
                    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 3]
                    if lines:
                        sheet_title = lines[0][:40]

                sheets.append({
                    "sheet": sheet_code,
                    "title": sheet_title,
                    "page_index": page_num
                })
            doc.close()
        except Exception:
            pass

        return sheets

    @staticmethod
    def get_package_files(project_id: str = "H8097") -> Dict[str, Any]:
        """Returns indexed primary drawing info and categorized companion references for a project."""
        pid = re.sub(r'[^a-zA-Z0-9_-]', '', (project_id or "H8097").upper().strip()) or "H8097"
        pdir = ProjectService.get_project_dir(pid)
        meta = ProjectService.get_project_meta(pid)

        # Primary drawing discovery
        dwg_dir = os.path.join(pdir, "drawing")
        dwg_files = [f for f in os.listdir(dwg_dir) if f.lower().endswith(('.pdf', '.dwg'))] if os.path.exists(dwg_dir) else []
        primary_name = dwg_files[0] if dwg_files else meta.get("primary_drawing", "")
        
        sheets_list = []
        if dwg_files:
            parsed = ProjectService.parse_pdf_sheets(os.path.join(dwg_dir, dwg_files[0]))
            sheets_list = parsed if parsed else [{"sheet": s.split(":")[0].replace("Sheet ", ""), "title": s.split(":")[-1].strip()} for s in meta.get("sheets", [])]
        elif meta.get("sheets"):
            sheets_list = [{"sheet": s.split(":")[0].replace("Sheet ", ""), "title": s.split(":")[-1].strip()} for s in meta.get("sheets", [])]

        primary_drawing = {
            "filename": primary_name or ("No primary drawing uploaded" if project_id != "H8097" else "H8097_AUSTINS FERRY_FC_05122025_Final PDF After QC validation.pdf"),
            "sheets_detected": sheets_list,
            "structure_type": meta.get("structure_type", "Telecom Structure"),
            "revision": meta.get("drawing_revision", "FOR CONSTRUCTION (Rev 1.0)")
        }

        # Prettify category labels
        cat_labels = {
            "FC_Drawing": "For-Construction Drawing",
            "FR": "FR (Feasibility Report)",
            "RLM": "RLM (Radio Link Model)",
            "Mount_Certificate": "Mount Structural Certificate",
            "Pole_Certificate": "Pole Structural Certificate",
            "Structural_Certificate": "Structural Assessment Certificate",
            "Structural_Drawings": "Structural Engineering Drawings",
            "SDV_Photos": "SDV Site Photos & Inspection",
            "As-built": "As-built Baseline Drawings",
            "Form_A": "Form A (Radiation Safety)",
            "Form_B": "Form B (EME Hazard Assessment)",
            "OSD": "OSD Standard Signage Drawings",
            "PDT": "Power Design Tool (PDT)",
            "PVA": "Power Viability Assessment (PVA)",
            "DPD": "Detailed Planning Diagram (DPD)",
            "RFNSA": "RFNSA National Site Database",
            "Environmental": "Environmental & Heritage Reports",
            "Geotech": "Geotechnical Soil Reports",
            "Survey": "Land Survey & Topography",
            "General_Companion": "General Engineering Companion"
        }

        # Multi-source scan across all reference package locations
        ref_dirs_to_check = [
            os.path.join(pdir, "references"),
            os.path.join(LEGACY_PROJECTS_DIR, pid, "references"),
            os.path.join(BASE_DIR, "qaInput", "reference_package"),
            REFERENCE_FILES_DIR,
            os.path.join(BASE_DIR, "reference_files")
        ]

        categories = {}
        seen_files = set()
        total_ref_files = 0

        for ref_dir in ref_dirs_to_check:
            if os.path.exists(ref_dir) and os.path.isdir(ref_dir):
                for root, _, files in os.walk(ref_dir):
                    for f in sorted(files):
                        if f in seen_files:
                            continue
                        fp = os.path.join(root, f)
                        if not os.path.isfile(fp):
                            continue
                        seen_files.add(f)
                        total_ref_files += 1
                        try:
                            size_kb = round(os.path.getsize(fp) / 1024, 1)
                        except Exception:
                            size_kb = 0.0
                        ext = os.path.splitext(f)[1].lower()
                        cat = classify_file(f)
                        cat_display = cat_labels.get(cat, cat.replace("_", " "))

                        if cat_display not in categories:
                            categories[cat_display] = []
                        categories[cat_display].append({
                            "name": f,
                            "size_kb": size_kb,
                            "extension": ext
                        })

        # Also query Backblaze B2 remote object storage under <pid>/references/
        try:
            from backend.services.storage_service import storage
            b2_files = storage.list_project_files(pid, "references")
            for b2_f in b2_files:
                fname = b2_f.get("name")
                if fname and fname not in seen_files:
                    seen_files.add(fname)
                    total_ref_files += 1
                    ext = os.path.splitext(fname)[1].lower()
                    cat = classify_file(fname)
                    cat_display = cat_labels.get(cat, cat.replace("_", " "))
                    if cat_display not in categories:
                        categories[cat_display] = []
                    categories[cat_display].append({
                        "name": fname,
                        "size_kb": b2_f.get("size_kb", 0.0),
                        "extension": ext
                    })
        except Exception as e:
            print(f"[ProjectService] Notice querying B2 references: {e}")

        category_list = []
        for cat_name, file_list in sorted(categories.items()):
            # Sort files within each category so core documents (PDF/XLSX) are listed first
            file_list.sort(key=lambda x: (0 if any(x.get("name", "").lower().endswith(ext) for ext in [".pdf", ".xlsx", ".xlsm", ".docx", ".dwg"]) else 1, x.get("name", "").lower()))
            category_list.append({
                "category": cat_name,
                "count": len(file_list),
                "files": file_list[:60]
            })

        return {
            "project_id": pid,
            "primary_drawing": primary_drawing,
            "reference_categories": category_list,
            "total_reference_files": total_ref_files
        }
