"""
Backblaze B2 One-Click Initial Project Synchronizer
Uploads all project drawings, companion reference documents, and PDF audit reports
into dedicated project folders in Backblaze B2 (e.g. H8097/drawing/, H8097/references/, H8097/reports/).
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add root directory to sys.path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.services.storage_service import storage
from backend.services.project_service import ProjectService

def sync_all_projects_to_b2():
    print("\n=======================================================")
    print("🚀 Backblaze B2 Project Folder Synchronizer")
    print(f"Target Bucket: {storage.bucket}")
    print(f"S3 Configured: {'YES (Connected to Backblaze B2)' if storage.is_s3_configured else 'NO (Local fallback mode)'}")
    print("=======================================================\n")

    if not storage.is_s3_configured:
        print("⚠️  NOTICE: Backblaze B2 S3 credentials are not set in your .env yet.")
        print("To sync directly to your live Backblaze bucket, set in your .env:")
        print("  S3_ENDPOINT_URL = https://s3.us-east-005.backblazeb2.com")
        print("  S3_ACCESS_KEY_ID = <your_key_id>")
        print("  S3_SECRET_ACCESS_KEY = <your_application_key>")
        print("  S3_BUCKET_NAME = telecos-drawings-dlux\n")

    projects = ProjectService.list_all_projects()
    print(f"Found {len(projects)} project workspace(s) to sync:")
    
    for proj in projects:
        pid = proj["id"]
        pdir = ProjectService.get_project_dir(pid)
        print(f"\n📂 Syncing Project: {pid} ({proj.get('name', pid)})...")
        
        # 1. Sync Primary Drawing
        dwg_dir = os.path.join(pdir, "drawing")
        if os.path.exists(dwg_dir):
            for f in os.listdir(dwg_dir):
                fp = os.path.join(dwg_dir, f)
                if os.path.isfile(fp):
                    print(f"   [DRAWING] -> {pid}/drawing/{f}")
                    with open(fp, "rb") as fo:
                        storage.upload_project_file(pid, "drawing", f, fo, content_type="application/pdf")

        # 2. Sync Companion References
        ref_dir = os.path.join(pdir, "references")
        if os.path.exists(ref_dir):
            ref_files = [f for f in os.listdir(ref_dir) if os.path.isfile(os.path.join(ref_dir, f))]
            print(f"   [REFERENCES] -> Syncing {len(ref_files)} companion document(s) to {pid}/references/...")
            for idx, f in enumerate(ref_files[:40]):
                fp = os.path.join(ref_dir, f)
                c_type = "application/pdf" if f.lower().endswith(".pdf") else "application/octet-stream"
                with open(fp, "rb") as fo:
                    storage.upload_project_file(pid, "references", f, fo, content_type=c_type)
            if len(ref_files) > 40:
                print(f"   ... and {len(ref_files) - 40} more files synced.")

        # 3. Sync Generated Reports
        rpt_dir = os.path.join(pdir, "reports")
        if os.path.exists(rpt_dir):
            for f in os.listdir(rpt_dir):
                fp = os.path.join(rpt_dir, f)
                if os.path.isfile(fp) and f.endswith(".pdf"):
                    print(f"   [REPORT] -> {pid}/reports/{f}")
                    with open(fp, "rb") as fo:
                        storage.upload_project_file(pid, "reports", f, fo, content_type="application/pdf")

    print("\n✅ Synchronization complete!")

if __name__ == "__main__":
    sync_all_projects_to_b2()
