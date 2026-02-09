"""
Tools for the Data Preparation Agent.
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from ..config import PLUTUS_BASE_URL, PLUTUS_API_KEY

async def get_order_info(
    order_id: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Retrieves order information from the Plutus server using the order ID.

    Args:
        order_id: The ID of the order to retrieve.
        tool_context: The tool context.

    Returns:
        Dict containing the order information or error details.
    """
    base_url = PLUTUS_BASE_URL
    api_key = PLUTUS_API_KEY

    if not base_url:
        return {"error": "PLUTUS_API_BASE_URL not set"}
    if not api_key:
        return {"error": "PLUTUS_API_KEY not set"}

    url = f"{base_url}/getOrder?orderId={order_id}"

    headers = {
        "X-Api-Key": api_key
    }

    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            error_body = e.read().decode("utf-8")
            return {"error": f"HTTP Error: {e.code} {e.reason}", "details": error_body}
        except Exception:
             return {"error": f"HTTP Error: {e.code} {e.reason}"}
    except urllib.error.URLError as e:
        return {"error": f"URL Error: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}

async def download_image(
    url: str,
    filename: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Downloads an image from a URL and saves it as an artifact.

    Args:
        url: The URL of the image to download.
        filename: The filename to save the artifact as (e.g., 'order_image.jpg').
        tool_context: The tool context.

    Returns:
        Dict containing success status and artifact filename.
    """
    try:
        # User-Agent header is often required by servers to accept requests from scripts
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req) as response:
            data = response.read()
            content_type = response.headers.get('Content-Type', 'image/jpeg') # Default to jpeg

            # Simple mapping if needed, but 'image/jpeg' etc works for types.Part usually
            mime_type = content_type.split(';')[0].strip()

            image_part = types.Part.from_bytes(data=data, mime_type=mime_type)
            await tool_context.save_artifact(filename=filename, artifact=image_part)

            return {
                "success": True,
                "artifact_name": filename,
                "message": f"Image downloaded from {url} and saved as {filename}"
            }

    except urllib.error.HTTPError as e:
         return {"success": False, "error": f"HTTP Error: {e.code} {e.reason}"}
    except urllib.error.URLError as e:
        return {"success": False, "error": f"URL Error: {e.reason}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Create tool instances
get_order_info_tool = FunctionTool(func=get_order_info)
download_image_tool = FunctionTool(func=download_image)
