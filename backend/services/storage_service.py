"""
Universal S3-Compatible Object Storage Service (Supports Backblaze B2, Cloudflare R2, AWS S3, and Local Disk Fallback).
Handles zero-RAM streaming uploads, presigned URLs, and persistent document storage.
"""
import os
import io
import re
import shutil
from typing import Optional, BinaryIO
import boto3
from botocore.config import Config

from backend.config import DB_DIR

class StorageService:
    def __init__(self):
        # Support Backblaze B2 / Generic S3 or Cloudflare R2 environment variables
        self.endpoint_url = os.getenv("S3_ENDPOINT_URL", "").strip()
        self.access_key = os.getenv("S3_ACCESS_KEY_ID", os.getenv("CF_R2_ACCESS_KEY_ID", "")).strip()
        self.secret_key = os.getenv("S3_SECRET_ACCESS_KEY", os.getenv("CF_R2_SECRET_ACCESS_KEY", "")).strip()
        self.bucket = os.getenv("S3_BUCKET_NAME", os.getenv("CF_R2_BUCKET_NAME", "telecos-drawings-dlux")).strip()
        self.region = os.getenv("S3_REGION", "us-east-005").strip()

        # Cloudflare R2 shorthand fallback
        account_id = os.getenv("CF_ACCOUNT_ID", "").strip()
        if not self.endpoint_url and account_id:
            self.endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
        elif self.endpoint_url and not self.endpoint_url.startswith("http"):
            self.endpoint_url = f"https://{self.endpoint_url}"

        self.is_s3_configured = bool(self.endpoint_url and self.access_key and self.secret_key)
        self.local_storage_root = os.path.join(DB_DIR, "storage")
        os.makedirs(self.local_storage_root, exist_ok=True)

        if self.is_s3_configured:
            self.s3 = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=Config(signature_version="s3v4"),
                region_name=self.region
            )
        else:
            self.s3 = None

    def upload_stream(self, file_obj: BinaryIO, key: str, content_type: str = "application/pdf") -> str:
        """Uploads a file-like stream to S3 / Backblaze B2 (or local disk fallback) with near 0 MB RAM consumption."""
        if self.is_s3_configured and self.s3:
            self.s3.upload_fileobj(
                file_obj,
                self.bucket,
                key,
                ExtraArgs={"ContentType": content_type}
            )
            return key
        else:
            # Local disk fallback
            dest_path = os.path.join(self.local_storage_root, key)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, "wb") as out_f:
                shutil.copyfileobj(file_obj, out_f)
            return key

    def upload_bytes(self, data: bytes, key: str, content_type: str = "application/pdf") -> str:
        """Uploads raw bytes to S3 or local disk."""
        return self.upload_stream(io.BytesIO(data), key, content_type=content_type)

    def get_presigned_download_url(self, key: str, expires_in: int = 3600) -> str:
        """Generates a secure presigned S3 download URL or local endpoint fallback."""
        if self.is_s3_configured and self.s3:
            return self.s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in
            )
        else:
            # In local fallback, serve via static API route
            return f"/api/storage/{key}"

    def upload_project_file(self, project_id: str, subfolder: str, filename: str, file_obj_or_bytes, content_type: str = "application/pdf") -> str:
        """Uploads a file to a specific project folder in Backblaze B2 (e.g. H8097/references/doc.pdf)."""
        pid = re.sub(r'[^a-zA-Z0-9_-]', '', (project_id or "H8097").upper().strip()) or "H8097"
        clean_sub = subfolder.strip("/").replace("\\", "/")
        clean_name = os.path.basename(filename)
        key = f"{pid}/{clean_sub}/{clean_name}"
        
        if isinstance(file_obj_or_bytes, (bytes, bytearray)):
            return self.upload_bytes(file_obj_or_bytes, key, content_type=content_type)
        else:
            return self.upload_stream(file_obj_or_bytes, key, content_type=content_type)

    def list_project_files(self, project_id: str, subfolder: str = "") -> list:
        """Lists all files stored under a project folder in Backblaze B2."""
        pid = re.sub(r'[^a-zA-Z0-9_-]', '', (project_id or "H8097").upper().strip()) or "H8097"
        prefix = f"{pid}/"
        if subfolder:
            prefix += f"{subfolder.strip('/')}/"

        files = []
        if self.is_s3_configured and self.s3:
            try:
                paginator = self.s3.get_paginator('list_objects_v2')
                for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                    for obj in page.get('Contents', []):
                        key = obj.get('Key', '')
                        if key and not key.endswith('/'):
                            fname = os.path.basename(key)
                            files.append({
                                "key": key,
                                "name": fname,
                                "size_bytes": obj.get('Size', 0),
                                "size_kb": round(obj.get('Size', 0) / 1024, 1),
                                "last_modified": str(obj.get('LastModified', ''))
                            })
            except Exception as e:
                print(f"[StorageService] Notice listing B2 objects for {prefix}: {e}")
        else:
            local_dir = os.path.join(self.local_storage_root, prefix)
            if os.path.exists(local_dir):
                for root, _, f_list in os.walk(local_dir):
                    for f in f_list:
                        fp = os.path.join(root, f)
                        rel_k = os.path.relpath(fp, self.local_storage_root).replace("\\", "/")
                        files.append({
                            "key": rel_k,
                            "name": f,
                            "size_bytes": os.path.getsize(fp),
                            "size_kb": round(os.path.getsize(fp) / 1024, 1),
                            "last_modified": ""
                        })
        return files

    def sync_project_directory(self, project_id: str, local_project_dir: str):
        """Syncs all files in a local project directory into Backblaze B2 under <project_id>/."""
        if not os.path.exists(local_project_dir):
            return
        
        pid = re.sub(r'[^a-zA-Z0-9_-]', '', (project_id or "H8097").upper().strip()) or "H8097"
        for sub in ("drawing", "references", "reports"):
            sub_path = os.path.join(local_project_dir, sub)
            if os.path.exists(sub_path):
                for root, _, files in os.walk(sub_path):
                    for f in files:
                        fp = os.path.join(root, f)
                        rel_sub = os.path.relpath(root, local_project_dir).replace("\\", "/")
                        try:
                            with open(fp, "rb") as f_obj:
                                c_type = "application/pdf" if f.lower().endswith(".pdf") else "application/octet-stream"
                                self.upload_project_file(pid, rel_sub, f, f_obj, content_type=c_type)
                        except Exception as e:
                            print(f"[StorageService] Notice syncing {f} to B2: {e}")

# Global singleton storage service
storage = StorageService()

