from __future__ import annotations
import os
from pathlib import Path
from urllib.request import Request, urlopen

def backend() -> str:
    return os.getenv("FASTWIKI_ATTACHMENT_BACKEND", "local").lower()

def _r2_client():
    import boto3
    from botocore.config import Config
    return boto3.client(
        "s3", endpoint_url=os.getenv("R2_ENDPOINT"),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        region_name=os.getenv("R2_REGION", "auto"),
        config=Config(signature_version="s3v4"),
    )

def put(key: str, body: bytes, content_type: str) -> str:
    selected = backend()
    if selected == "r2":
        _r2_client().put_object(Bucket=os.environ["R2_BUCKET"], Key=key, Body=body, ContentType=content_type)
        return key
    if selected == "fastdrive":
        endpoint = os.getenv("FASTDRIVE_UPLOAD_URL", "")
        token = os.getenv("FASTDRIVE_SERVICE_TOKEN", "")
        if not endpoint or not token:
            raise RuntimeError("FastDrive storage requires FASTDRIVE_UPLOAD_URL and FASTDRIVE_SERVICE_TOKEN")
        request = Request(endpoint, data=body, method="POST", headers={
            "Authorization": f"Bearer {token}", "Content-Type": content_type,
            "X-Filename": key,
        })
        with urlopen(request, timeout=30) as response:
            if response.status >= 300:
                raise RuntimeError("FastDrive upload failed")
        return key
    root = Path(os.getenv("FASTWIKI_UPLOAD_DIR", "data/uploads"))
    target = root / key
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    return key

def get(key: str) -> bytes:
    if backend() == "r2":
        return _r2_client().get_object(Bucket=os.environ["R2_BUCKET"], Key=key)["Body"].read()
    root = Path(os.getenv("FASTWIKI_UPLOAD_DIR", "data/uploads"))
    return (root / key).read_bytes()

