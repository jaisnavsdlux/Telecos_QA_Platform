"""
Universal S3-Compatible Object Storage Service (Supports Backblaze B2, Cloudflare R2, AWS S3, and Local Disk Fallback).
Handles zero-RAM streaming uploads, presigned URLs, and persistent document storage.
"""
import os
import io
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

    def download_to_path(self, key: str, target_path: str) -> bool:
        """Downloads an object from S3 or local storage to a local file path."""
        if self.is_s3_configured and self.s3:
            try:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                self.s3.download_file(self.bucket, key, target_path)
                return True
            except Exception:
                return False
        else:
            src = os.path.join(self.local_storage_root, key)
            if os.path.exists(src):
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(src, target_path)
                return True
            return False

# Global singleton storage service
storage = StorageService()
