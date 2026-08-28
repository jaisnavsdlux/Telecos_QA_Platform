"""
Cloudflare R2 Object Storage Service (S3-Compatible) with Local Disk Fallback.
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
        self.account_id = os.getenv("CF_ACCOUNT_ID", "").strip()
        self.access_key = os.getenv("CF_R2_ACCESS_KEY_ID", "").strip()
        self.secret_key = os.getenv("CF_R2_SECRET_ACCESS_KEY", "").strip()
        self.bucket = os.getenv("CF_R2_BUCKET_NAME", "telecos-drawings").strip()

        self.is_r2_configured = bool(self.account_id and self.access_key and self.secret_key)
        self.local_storage_root = os.path.join(DB_DIR, "storage")
        os.makedirs(self.local_storage_root, exist_ok=True)

        if self.is_r2_configured:
            self.s3 = boto3.client(
                "s3",
                endpoint_url=f"https://{self.account_id}.r2.cloudflarestorage.com",
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=Config(signature_version="s3v4"),
                region_name="auto"
            )
        else:
            self.s3 = None

    def upload_stream(self, file_obj: BinaryIO, key: str, content_type: str = "application/pdf") -> str:
        """Uploads a file-like stream to Cloudflare R2 (or local disk fallback) with near 0 MB RAM consumption."""
        if self.is_r2_configured and self.s3:
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
        """Uploads raw bytes to Cloudflare R2 or local disk."""
        return self.upload_stream(io.BytesIO(data), key, content_type=content_type)

    def get_presigned_download_url(self, key: str, expires_in: int = 3600) -> str:
        """Generates a secure presigned Cloudflare R2 download URL or local endpoint fallback."""
        if self.is_r2_configured and self.s3:
            return self.s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in
            )
        else:
            # In local fallback, serve via static API route
            return f"/api/storage/{key}"

    def download_to_path(self, key: str, target_path: str) -> bool:
        """Downloads an object from R2 or local storage to a local file path."""
        if self.is_r2_configured and self.s3:
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
