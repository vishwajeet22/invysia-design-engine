"""
Publisher tools for the Daedalus pipeline.

These tools allow the Publisher Agent to upload the generated website to an S3-compatible storage.
"""

import os
from pathlib import Path
from typing import Dict, Any
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from ..config import s3_client

CONTENT_TYPES = {
    ".html": "text/html",
    ".js": "application/javascript",
    ".css": "text/css",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".svg": "image/svg+xml"
}

def content_type(path: str) -> str:
    for ext, ct in CONTENT_TYPES.items():
        if path.endswith(ext):
            return ct
    return "application/octet-stream"

async def upload_site_to_s3(
    site_path: str,
    tool_context: ToolContext,
    slug: str = None
) -> Dict[str, Any]:
    """
    Uploads the generated website to S3.

    Args:
        site_path: The local path to the website folder.
        tool_context: The ToolContext.
        slug: The unique identifier for the site (used as S3 key prefix).

    Returns:
        Dict containing success status and public URL if available (or message).
    """
    try:
        bucket_name = os.environ.get("BUCKET_NAME", "demo-assets")

        # We assume standard AWS env vars are set:
        # AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION (optional)

        if not bucket_name:
            return {"success": False, "error": "BUCKET_NAME environment variable is not set."}

        # Use global S3 client
        s3 = s3_client

        base_path = Path(site_path)
        if not base_path.exists():
            return {"success": False, "error": f"Site path {site_path} does not exist."}

        # Get the output directory name (e.g., "output_1770269243")
        output_dir_name = slug if slug else base_path.name

        uploaded_files = []

        # Walk through the directory
        for root, _, files in os.walk(base_path):
            for file in files:
                local_path = Path(root) / file
                relative_path = local_path.relative_to(base_path)

                # Convert path to string and ensure forward slashes for S3 key
                # Include output directory name as prefix: output_xxx/file.html
                r2_key = f"{output_dir_name}/{str(relative_path).replace(os.sep, '/')}"

                ct = content_type(str(local_path))

                # Determine cache control
                cache_control = "public, max-age=31536000, immutable"
                if file == "index.html" or str(local_path).endswith(".html"):
                     cache_control = "max-age=60"

                try:
                    s3.upload_file(
                        str(local_path),
                        bucket_name,
                        r2_key,
                        ExtraArgs={
                            "ContentType": ct,
                            "CacheControl": cache_control
                        }
                    )
                    uploaded_files.append(r2_key)
                except Exception as e:
                    print(f"Failed to upload {r2_key}: {e}")
                    return {"success": False, "error": f"Failed to upload {r2_key}: {e}"}

        return {
            "success": True,
            "message": f"Successfully uploaded {len(uploaded_files)} files to {bucket_name}.",
            "uploaded_files": uploaded_files
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

# Tool instances
upload_to_s3_tool = FunctionTool(func=upload_site_to_s3)
