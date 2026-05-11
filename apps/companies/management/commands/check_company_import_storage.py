"""
Verify the company-import storage backend is healthy and correctly configured.

Local-dev mode (STORAGE_AWS=False):
  Checks that COMPANY_IMPORT_LOCAL_PATH exists, is a directory, and is writable.

S3/Spaces mode (STORAGE_AWS=True):
  1. HEAD the bucket to confirm it exists and credentials are valid.
  2. Probe CORS with a synthetic OPTIONS preflight from the production origin.
  3. Generate a presigned PUT URL, upload a 1-byte probe, then DELETE it —
     confirms the IAM user has s3:PutObject and s3:DeleteObject on the prefix.

Exit code 0 = all checks passed. Exit code 1 = one or more checks failed.
"""
import os
import urllib.request
import urllib.error

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from django.conf import settings
from django.core.management.base import BaseCommand

_PRODUCTION_ORIGIN = "https://fastjob.apps.darideveloper.com"
_PROBE_KEY_SUFFIX = "_health_probe/probe.bin"


class Command(BaseCommand):
    help = "Assert company-import storage backend is healthy and CORS-configured."

    def handle(self, *args, **options):
        if not getattr(settings, "STORAGE_AWS", False):
            self._check_local()
        else:
            self._check_s3()

    # ------------------------------------------------------------------
    # Local-dev path
    # ------------------------------------------------------------------

    def _check_local(self):
        path = settings.COMPANY_IMPORT_LOCAL_PATH
        issues = []

        if not os.path.exists(path):
            issues.append(f"Path does not exist: {path}")
        elif not os.path.isdir(path):
            issues.append(f"Path is not a directory: {path}")
        elif not os.access(path, os.W_OK):
            issues.append(f"Path is not writable: {path}")

        if issues:
            for issue in issues:
                self.stderr.write(self.style.WARNING(f"[WARN] {issue}"))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS(f"[OK] COMPANY_IMPORT_LOCAL_PATH={path}"))

    # ------------------------------------------------------------------
    # S3 / Spaces path
    # ------------------------------------------------------------------

    def _check_s3(self):
        issues = []
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        prefix = settings.IMPORTS_LOCATION
        probe_key = f"{prefix}/{_PROBE_KEY_SUFFIX}"

        s3 = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL or None,
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        # 1. HEAD bucket
        try:
            s3.head_bucket(Bucket=bucket)
            self.stdout.write(self.style.SUCCESS(f"[OK] Bucket exists: {bucket}"))
        except (ClientError, BotoCoreError) as exc:
            issues.append(f"Bucket HEAD failed: {exc}")

        # 2. Probe CORS via OPTIONS preflight
        if not issues:
            endpoint = settings.AWS_S3_ENDPOINT_URL or f"https://s3.amazonaws.com"
            cors_url = f"{endpoint}/{bucket}/"
            try:
                req = urllib.request.Request(cors_url, method="OPTIONS")
                req.add_header("Origin", _PRODUCTION_ORIGIN)
                req.add_header("Access-Control-Request-Method", "PUT")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    allow_methods = resp.headers.get("Access-Control-Allow-Methods", "")
                if "PUT" in allow_methods or "*" in allow_methods:
                    self.stdout.write(self.style.SUCCESS("[OK] CORS: PUT allowed"))
                else:
                    issues.append(
                        f"CORS preflight returned Access-Control-Allow-Methods={allow_methods!r}; "
                        f"PUT not listed. Apply the CORS rule from design.md D2."
                    )
            except urllib.error.HTTPError as exc:
                allow_methods = exc.headers.get("Access-Control-Allow-Methods", "")
                if "PUT" in allow_methods or "*" in allow_methods:
                    self.stdout.write(self.style.SUCCESS("[OK] CORS: PUT allowed"))
                else:
                    issues.append(f"CORS preflight HTTP error {exc.code}: {exc}")
            except Exception as exc:
                issues.append(f"CORS preflight request failed: {exc}")

        # 3. Presigned PUT roundtrip (write + delete probe object)
        if not issues:
            try:
                url = s3.generate_presigned_url(
                    "put_object",
                    Params={"Bucket": bucket, "Key": probe_key, "ContentType": "application/octet-stream"},
                    ExpiresIn=60,
                    HttpMethod="PUT",
                )
                req = urllib.request.Request(url, data=b"\x00", method="PUT")
                req.add_header("Content-Type", "application/octet-stream")
                with urllib.request.urlopen(req, timeout=15):
                    pass
                self.stdout.write(self.style.SUCCESS("[OK] Presigned PUT: probe uploaded"))

                s3.delete_object(Bucket=bucket, Key=probe_key)
                self.stdout.write(self.style.SUCCESS("[OK] Presigned PUT: probe deleted"))
            except Exception as exc:
                issues.append(f"Presigned PUT roundtrip failed: {exc}")

        if issues:
            for issue in issues:
                self.stderr.write(self.style.ERROR(f"[FAIL] {issue}"))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS("[OK] All S3 import storage checks passed."))
