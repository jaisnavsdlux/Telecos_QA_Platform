import os
import sys
import time
import json
import shutil
import glob
from datetime import datetime
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

from backend.config import PROJECTS_DIR, REPORTS_DIR, RULES_DIR, DB_DIR, BASE_DIR
from backend.services.project_service import classify_file, ProjectService
from backend.reference_validator.validator.rule_engine import load_rules, get_token_logs
from backend.reference_validator.main import run_validation
from backend.report_generator import generate_report
from backend.database.connection import SessionLocal
from backend.database.models import ValidationRun, RuleVerdict, TokenUsageLog

def main(project_id="H8097", progress_callback=None):
    pid = (project_id or "H8097").upper().strip()
    print("=" * 80)
    print(f"🚀 RUNNING VALIDATION FOR PROJECT: {pid}")
    print(f"Model: {os.getenv('LLM_MODEL', 'gemini-2.0-flash')}")
    print("=" * 80)

    # 1. Build Reference Mapping dynamically across uploaded project directories
    ref_dirs_to_check = [
        os.path.join(PROJECTS_DIR, pid, "references"),
        os.path.join("projects", pid, "references"),
        os.path.join(DB_DIR, "reference_files"),
        "reference_files",
        os.path.join("qaInput", "reference_package")
    ]
    
    ref_mapping = {}
    total_ref_files = 0
    for rdir in ref_dirs_to_check:
        if os.path.exists(rdir) and os.path.isdir(rdir):
            for root, _, files in os.walk(rdir):
                for f in files:
                    fpath = os.path.join(root, f)
                    if os.path.isfile(fpath):
                        tag = classify_file(f)
                        if tag not in ("Unknown", "FC_Drawing"):
                            if tag not in ref_mapping:
                                ref_mapping[tag] = []
    # If references are missing locally (e.g. fresh Render container deployment), pull from Backblaze B2
    if total_ref_files < 10:
        try:
            from backend.services.storage_service import storage
            if storage.is_s3_configured:
                b2_refs = storage.list_project_files(pid, "references")
                ref_dest_dir = os.path.join(PROJECTS_DIR, pid, "references")
                os.makedirs(ref_dest_dir, exist_ok=True)
                for item in b2_refs:
                    fname = item.get("name") or item.get("filename")
                    if fname:
                        dst_path = os.path.join(ref_dest_dir, fname)
                        if not os.path.exists(dst_path):
                            storage.s3.download_file(storage.bucket, f"{pid}/references/{fname}", dst_path)
                            tag = classify_file(fname)
                            if tag not in ("Unknown", "FC_Drawing"):
                                if tag not in ref_mapping:
                                    ref_mapping[tag] = []
                                if dst_path not in ref_mapping[tag]:
                                    ref_mapping[tag].append(dst_path)
                                    total_ref_files += 1
        except Exception as b2_dl_err:
            print(f"Notice fetching references from B2: {b2_dl_err}")

    print(f"\n[1/4] Constructed Reference Mapping for {len(ref_mapping)} Document Categories ({total_ref_files} files found):")
    for tag, paths in sorted(ref_mapping.items()):
        print(f"  • {tag:<22} -> {len(paths)} file(s)")

    # 2. Select target drawing PDF
    # 2. Select target drawing PDF (Prioritize FC Child CAD drawings in project drawing folder)
    drawing_dirs_to_check = [
        os.path.join(PROJECTS_DIR, pid, "drawing"),
        os.path.join(BASE_DIR, "qaInput", "primary_drawing"),
        os.path.join("projects", pid, "drawing"),
        os.path.join(DB_DIR, "drawings"),
        "drawings"
    ]
    
    candidates = []
    for ddir in drawing_dirs_to_check:
        if os.path.exists(ddir) and os.path.isdir(ddir):
            for root, _, files in os.walk(ddir):
                for f in files:
                    if f.lower().endswith(".pdf"):
                        fp = os.path.join(root, f)
                        try:
                            sz = os.path.getsize(fp)
                            if sz > 20000 and not f.lower().startswith(f"{pid.lower()}_drawing.pdf"):
                                # Score candidate: prioritize FC / Child / Drawing keywords
                                score = sz
                                fname_upper = f.upper()
                                if "CHILD" in fname_upper or "FC" in fname_upper or "CAD" in fname_upper:
                                    score += 100_000_000 # High priority for actual FC CAD drawing
                                candidates.append((score, fp, f))
                        except Exception:
                            pass

    # If no local CAD file found, check Backblaze B2 storage
    if not candidates:
        try:
            from backend.services.storage_service import storage
            b2_drawings = storage.list_project_files(pid, "drawing")
            if b2_drawings:
                target_b2 = b2_drawings[0]["name"]
                local_dst = os.path.join(PROJECTS_DIR, pid, "drawing", target_b2)
                os.makedirs(os.path.dirname(local_dst), exist_ok=True)
                storage.s3.download_file(storage.bucket, f"{pid}/drawing/{target_b2}", local_dst)
                candidates.append((os.path.getsize(local_dst), local_dst, target_b2))
        except Exception as e:
            print(f"Notice downloading drawing from B2: {e}")

    pdf_path = None
    if candidates:
        # Pick the highest-scored CAD PDF drawing (actual FC Child CAD Package)
        candidates.sort(key=lambda x: x[0], reverse=True)
        pdf_path = candidates[0][1]
    else:
        # Fallback only if absolutely no files exist
        os.makedirs(os.path.join(PROJECTS_DIR, pid, "drawing"), exist_ok=True)
        pdf_path = os.path.join(PROJECTS_DIR, pid, "drawing", f"{pid}_Drawing.pdf")
        if not os.path.exists(pdf_path):
            import fitz
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 50), f"Strelza QA Validation — Project {pid}")
            doc.save(pdf_path)
            doc.close()

    pdf_name = os.path.basename(pdf_path)
    try:
        sz_mb = round(os.path.getsize(pdf_path) / (1024 * 1024), 2)
    except Exception:
        sz_mb = 0.0
    print(f"\n[2/4] Target CAD Drawing: {pdf_name} ({sz_mb} MB)")

    # 3. Load rules
    rules_dict = load_rules("optus")
    rules_list = list(rules_dict.values())
    total_rules = len(rules_list)
    print(f"[3/4] Loaded {total_rules} active compliance rules")

    # 4. Progress callback
    start_time = time.time()
    def on_progress(current, total, current_res=None):
        pct = (current / total) * 100
        elapsed = time.time() - start_time
        print(f"  [{current:02d}/{total:02d}] ({pct:5.1f}%) Validated rule in {elapsed:.1f}s total...")
        if progress_callback:
            try:
                progress_callback(current, total, current_res, elapsed)
            except Exception as e:
                print(f"[on_progress callback error]: {e}")

    # 5. Run validation with full reference mapping
    print(f"\n[4/4] Executing AI Validation for all {total_rules} rules...")
    results = run_validation(
        pdf_path=pdf_path,
        rules=rules_list,
        reference_mapping=ref_mapping,
        use_cache=False,
        on_progress=on_progress
    )

    elapsed_total = time.time() - start_time
    print(f"\nValidation completed in {elapsed_total:.2f} seconds.")

    # 6. Generate PDF Report with unique timestamp
    os.makedirs(REPORTS_DIR, exist_ok=True)
    proj_reports_dir = os.path.join(PROJECTS_DIR, pid, "reports")
    os.makedirs(proj_reports_dir, exist_ok=True)
    
    ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"{pid}_Audit_Report_{ts_str}.pdf"
    timestamped_report = os.path.join(REPORTS_DIR, report_filename)
    project_report = os.path.join(proj_reports_dir, report_filename)
    output_report = os.path.join(REPORTS_DIR, "report_full_package.pdf")
    
    results_payload = {"results": results}
    generate_report(results_payload, timestamped_report, pdf_name)
    shutil.copy2(timestamped_report, project_report)
    shutil.copy2(timestamped_report, output_report)
    print(f"  ✓ Saved Timestamped PDF Report to: {timestamped_report}")
    print(f"  ✓ Synced Project Report to: {project_report}")

    # Stream generated report to Backblaze B2 under <project_id>/reports/
    try:
        from backend.services.storage_service import storage
        with open(timestamped_report, "rb") as rf:
            storage.upload_project_file(pid, "reports", os.path.basename(timestamped_report), rf, content_type="application/pdf")
        print(f"  ✓ Uploaded Report to Backblaze B2: {pid}/reports/{os.path.basename(timestamped_report)}")
    except Exception as b2_err:
        print(f"  Notice uploading report to B2: {b2_err}")

    # 7. Update Project Metadata & Persist to Neon PostgreSQL Database
    verdicts = {"PASS": 0, "FAIL": 0, "UNCLEAR": 0, "NOT_APPLICABLE": 0}
    for r in results:
        v = r.get("verdict", "UNCLEAR").upper()
        verdicts[v] = verdicts.get(v, 0) + 1

    try:
        meta = ProjectService.get_project_meta(pid)
        meta["latest_verdict"] = {
            "pass": verdicts.get("PASS", 0),
            "fail": verdicts.get("FAIL", 0),
            "unclear": verdicts.get("UNCLEAR", 0),
            "na": verdicts.get("NOT_APPLICABLE", 0),
            "total": total_rules
        }
        ProjectService.save_project_meta(pid, meta)
        
        # Save companion JSON
        meta_json_path = timestamped_report.replace(".pdf", ".json")
        with open(meta_json_path, "w", encoding="utf-8") as jf:
            json.dump({
                "verdict_summary": meta["latest_verdict"],
                "elapsed_seconds": round(elapsed_total, 2),
                "timestamp": ts_str
            }, jf, indent=2)
        shutil.copy2(meta_json_path, project_report.replace(".pdf", ".json"))
    except Exception as m_err:
        print("Project meta update notice:", m_err)

    try:
        with SessionLocal() as db:
            run_record = ValidationRun(
                id=f"run_{pid}_{ts_str}",
                project_id=pid,
                status="completed",
                model=os.getenv("LLM_MODEL", "gemini-2.0-flash"),
                elapsed_seconds=round(elapsed_total, 2),
                pass_count=verdicts.get("PASS", 0),
                fail_count=verdicts.get("FAIL", 0),
                unclear_count=verdicts.get("UNCLEAR", 0),
                na_count=verdicts.get("NOT_APPLICABLE", 0),
                total_rules=total_rules,
                report_filename=report_filename
            )
            db.add(run_record)
            
            for r in results:
                verdict_entry = RuleVerdict(
                    run_id=run_record.id,
                    rule_code=r.get("rule_id", "R000"),
                    verdict=r.get("verdict", "PASS"),
                    confidence=float(r.get("confidence", 0.95) if isinstance(r.get("confidence"), (int, float)) else 0.95),
                    reasoning=str(r.get("reasoning") or r.get("observation") or "")[:1000],
                    evidence_data=r.get("evidence", {}) if isinstance(r.get("evidence"), dict) else {"text": str(r.get("evidence", ""))}
                )
                db.add(verdict_entry)

            db.commit()
            print("  ✓ Run and verdicts persisted to Neon PostgreSQL Database.")
    except Exception as db_err:
        print(f"Notice: Database sync notice: {db_err}")

    # 8. Summary printout
    print("\n" + "=" * 80)
    print("📊 FULL PACKAGE VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total Rules Audited: {len(results)}")
    print(f"  ✓ PASS:           {verdicts.get('PASS', 0)}")
    print(f"  ✗ FAIL:           {verdicts.get('FAIL', 0)}")
    print(f"  ? UNCLEAR:        {verdicts.get('UNCLEAR', 0)}")
    print(f"  - NOT_APPLICABLE: {verdicts.get('NOT_APPLICABLE', 0)}")
    print("=" * 80)
    return results

if __name__ == "__main__":
    main()
