"""
Coding tools for the Daedalus pipeline.

These tools allow the Coding Agent to persist the generated website to the filesystem.
"""

import os
import time
from pathlib import Path
from typing import Dict, Any, List

from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

async def initialize_site_directory(
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Creates a timestamped output directory for the website generation.

    Args:
        tool_context: The ToolContext.

    Returns:
        Dict containing the success status and the absolute path to the created directory.
    """
    try:
        # Generate timestamp
        timestamp = int(time.time())
        dirname = f"output_{timestamp}"

        # Determine base path (relative to agents/daedalus/ which is the "agent directory" usually)
        # Assuming execution from repo root, agents/daedalus/ is a safe place.
        # But we want to be sure where we are.
        # Let's use the current working directory relative path if possible, or hardcode logical path.
        # The user said: "create a temp path in the parent directory of Daedalus agent with prefix output_"
        # Daedalus agent file is at agents/daedalus/agent.py. Parent dir of agent is agents/daedalus/.

        base_dir = Path(".")
        output_dir = base_dir / dirname
        assets_dir = output_dir / "assets"

        output_dir.mkdir(parents=True, exist_ok=True)
        assets_dir.mkdir(parents=True, exist_ok=True)

        return {
            "success": True,
            "path": str(output_dir.resolve()),
            "assets_path": str(assets_dir.resolve()),
            "message": f"Initialized output directory at {output_dir}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

async def save_code_file(
    base_path: str,
    filename: str,
    content: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Saves a code file (HTML, CSS, JS) to the specified base path.

    Args:
        base_path: The root directory for the website (returned by initialize_site_directory).
        filename: The relative filename (e.g., 'index.html', 'css/style.css').
        content: The text content of the file.
        tool_context: The ToolContext.

    Returns:
        Dict containing success status.
    """
    try:
        base = Path(base_path)
        if not base.exists():
             return {"success": False, "error": f"Base path {base_path} does not exist."}

        file_path = base / filename

        # Ensure parent directories exist (e.g. if filename is css/style.css)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(content, encoding='utf-8')

        return {
            "success": True,
            "filepath": str(file_path),
            "message": f"Saved {filename}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

async def export_site_assets(
    base_path: str,
    asset_map: Dict[str, str],
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Exports assets from artifacts to the local assets directory.

    Args:
        base_path: The root directory for the website.
        asset_map: A dictionary mapping asset_id to artifact_filename.
                   e.g., {"img-bg": "background.png"}
        tool_context: The ToolContext.

    Returns:
        Dict containing success status and a new map of asset_id -> relative_file_path.
    """
    try:
        base = Path(base_path)
        assets_dir = base / "assets"
        if not assets_dir.exists():
            assets_dir.mkdir(parents=True, exist_ok=True)

        new_map = {}

        for asset_id, artifact_name in asset_map.items():
            try:
                # Load artifact
                part = await tool_context.load_artifact(filename=artifact_name)

                if not part:
                    print(f"Warning: Artifact {artifact_name} not found.")
                    continue

                # Determine data and extension
                data = None
                ext = ".bin"

                if hasattr(part, 'inline_data') and part.inline_data:
                    data = part.inline_data.data
                    mime = part.inline_data.mime_type
                    # Simple mime to ext mapping
                    if mime == "image/png": ext = ".png"
                    elif mime == "image/jpeg": ext = ".jpg"
                    elif mime == "image/webp": ext = ".webp"
                    elif mime == "text/plain": ext = ".txt"
                    elif mime == "text/css": ext = ".css"
                    elif mime == "text/javascript": ext = ".js"
                    elif mime == "text/html": ext = ".html"
                    else:
                        # Try to infer from artifact name
                        if "." in artifact_name:
                            ext = Path(artifact_name).suffix

                # Fallback to text if inline_data is missing but text is present
                elif hasattr(part, 'text') and part.text:
                    data = part.text.encode('utf-8')
                    ext = ".txt"
                    if "." in artifact_name:
                         ext = Path(artifact_name).suffix

                if data:
                    # Use original filename if possible, or construct one
                    # We prefer the artifact name as the filename in the assets folder
                    target_filename = artifact_name
                    target_path = assets_dir / target_filename

                    target_path.write_bytes(data)

                    # Store relative path for HTML usage
                    # e.g. "assets/background.png"
                    new_map[asset_id] = f"assets/{target_filename}"
                else:
                    print(f"Warning: No data found for artifact {artifact_name}")

            except Exception as e:
                print(f"Error exporting asset {asset_id} ({artifact_name}): {e}")

        return {
            "success": True,
            "asset_paths": new_map,
            "message": f"Exported {len(new_map)} assets."
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

# Tool instances
initialize_site_tool = FunctionTool(func=initialize_site_directory)
save_code_tool = FunctionTool(func=save_code_file)
export_assets_tool = FunctionTool(func=export_site_assets)
