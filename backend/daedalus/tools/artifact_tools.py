"""
Artifact tools for the Daedalus wedding website design pipeline.

This module provides helper functions for saving and loading image artifacts
using ADK's artifact system, enabling image sharing between agents and tools.
"""

from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from pathlib import Path
from typing import Optional, Dict, Any


async def save_image_artifact(
    image_path: str,
    artifact_name: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Save a local image file as an artifact for sharing between agents.
    
    Args:
        image_path: Path to the local image file to save
        artifact_name: Name to use for the artifact (e.g., 'background_image.png')
        tool_context: The ToolContext for artifact operations
        
    Returns:
        Dict containing success status, artifact name, version, and metadata
    """
    path = Path(image_path)
    if not path.exists():
        return {"success": False, "error": f"Image file not found: {image_path}"}
    
    # Determine MIME type from extension
    mime_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.tiff': 'image/tiff',
        '.tif': 'image/tiff'
    }
    mime_type = mime_map.get(path.suffix.lower(), 'application/octet-stream')
    
    # Read image bytes and create Part
    image_bytes = path.read_bytes()
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    
    # Save as artifact
    version = await tool_context.save_artifact(filename=artifact_name, artifact=image_part)
    
    return {
        "success": True,
        "artifact_name": artifact_name,
        "version": version,
        "mime_type": mime_type,
        "size_bytes": len(image_bytes)
    }


async def save_text_artifact(
    text: str,
    artifact_name: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Save text content as an artifact.

    Args:
        text: The text content to save
        artifact_name: Name to use for the artifact (e.g., 'background_prompt.txt')
        tool_context: The ToolContext for artifact operations

    Returns:
        Dict containing success status and artifact name
    """
    try:
        text_bytes = text.encode('utf-8')
        part = types.Part.from_bytes(data=text_bytes, mime_type="text/plain")
        await tool_context.save_artifact(filename=artifact_name, artifact=part)
        return {"success": True, "artifact_name": artifact_name}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def load_text_artifact(
    artifact_name: str,
    tool_context: ToolContext,
    version: Optional[int] = None
) -> Dict[str, Any]:
    """
    Load a text artifact by name.

    Args:
        artifact_name: Name of the artifact to load (e.g., 'data.json')
        tool_context: The ToolContext for artifact operations
        version: Specific version to load (optional, defaults to latest)

    Returns:
        Dict containing success status, content, or error.
    """
    part = await tool_context.load_artifact(filename=artifact_name, version=version)

    if not part:
        return {"success": False, "error": f"Artifact '{artifact_name}' not found"}

    content = ""
    if hasattr(part, 'text') and part.text:
        content = part.text
    elif hasattr(part, 'inline_data') and part.inline_data and part.inline_data.data:
        try:
            content = part.inline_data.data.decode('utf-8')
        except Exception as e:
            return {"success": False, "error": f"Failed to decode artifact content: {str(e)}"}
    else:
        return {"success": False, "error": "Artifact does not contain text or inline data"}

    return {
        "success": True,
        "artifact_name": artifact_name,
        "content": content
    }


async def load_image_artifact(
    artifact_name: str,
    tool_context: ToolContext,
    version: Optional[int] = None
) -> Dict[str, Any]:
    """
    Load an image artifact by name.
    
    Args:
        artifact_name: Name of the artifact to load (e.g., 'aesthetics_guide.png')
        tool_context: The ToolContext for artifact operations
        version: Specific version to load (optional, defaults to latest)
        
    Returns:
        Dict containing success status, artifact name, and the image Part object
    """
    image_part = await tool_context.load_artifact(filename=artifact_name, version=version)
    
    if not image_part:
        return {"success": False, "error": f"Artifact '{artifact_name}' not found"}
    
    mime_type = None
    if image_part.inline_data:
        mime_type = image_part.inline_data.mime_type
    
    return {
        "success": True,
        "artifact_name": artifact_name,
        "image_part": image_part,
        "mime_type": mime_type
    }


# @deprecated - This function is deprecated and should not be used in new code.
async def save_image_bytes_artifact(
    image_bytes: bytes,
    artifact_name: str,
    mime_type: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Save raw image bytes as an artifact.
    
    Args:
        image_bytes: Raw bytes of the image
        artifact_name: Name to use for the artifact
        mime_type: MIME type of the image (e.g., 'image/png')
        tool_context: The ToolContext for artifact operations
        
    Returns:
        Dict containing success status, artifact name, and version
    """
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    
    version = await tool_context.save_artifact(filename=artifact_name, artifact=image_part)
    
    return {
        "success": True,
        "artifact_name": artifact_name,
        "version": version,
        "mime_type": mime_type,
        "size_bytes": len(image_bytes)
    }


async def list_image_artifacts(tool_context: ToolContext) -> Dict[str, Any]:
    """
    List all available artifacts in the current session.
    
    Args:
        tool_context: The ToolContext for artifact operations
        
    Returns:
        Dict containing list of artifact names
    """
    artifacts = await tool_context.list_artifacts()
    
    return {
        "success": True,
        "artifacts": artifacts
    }


# @deprecated - This function is deprecated and should not be used in new code.
async def save_user_image_as_artifact(
    artifact_name: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Save an image from the user's message as an artifact.
    
    This tool extracts images that the user has sent in the conversation
    and saves them as artifacts. Use this when a user provides an image
    directly in chat that needs to be stored for later use.
    
    Args:
        artifact_name: Name to save the artifact as (e.g., 'aesthetics_guide.png')
        tool_context: The ToolContext for artifact operations
        
    Returns:
        Dict containing success status and artifact details
    """
    user_image_part = None
    
    # First, try to get the image from the current user_content in the tool context
    # ToolContext inherits from CallbackContext which has user_content
    if hasattr(tool_context, 'user_content') and tool_context.user_content:
        user_content = tool_context.user_content
        if hasattr(user_content, 'parts') and user_content.parts:
            for part in user_content.parts:
                # Check if this part contains inline image data
                if hasattr(part, 'inline_data') and part.inline_data:
                    if hasattr(part.inline_data, 'mime_type') and part.inline_data.mime_type:
                        if part.inline_data.mime_type.startswith('image/'):
                            user_image_part = part
                            break
    
    # If not found in user_content, try to find it in the session events
    if not user_image_part:
        try:
            invocation_context = tool_context.invocation_context
            session = invocation_context.session
            
            # Check the session events for user messages with images
            if hasattr(session, 'events') and session.events:
                # Iterate through events in reverse (most recent first)
                for event in reversed(session.events):
                    if hasattr(event, 'author') and event.author == 'user':
                        if hasattr(event, 'content') and event.content:
                            if hasattr(event.content, 'parts') and event.content.parts:
                                for part in event.content.parts:
                                    if hasattr(part, 'inline_data') and part.inline_data:
                                        if hasattr(part.inline_data, 'mime_type') and part.inline_data.mime_type:
                                            if part.inline_data.mime_type.startswith('image/'):
                                                user_image_part = part
                                                break
                                if user_image_part:
                                    break
        except Exception as e:
            # If session access fails, continue without it
            pass
    
    if not user_image_part:
        return {
            "success": False,
            "error": "No image found in the user's message. Please ensure the user has sent an image."
        }
    
    # Save the image as an artifact
    mime_type = user_image_part.inline_data.mime_type
    version = await tool_context.save_artifact(filename=artifact_name, artifact=user_image_part)
    
    return {
        "success": True,
        "artifact_name": artifact_name,
        "version": version,
        "mime_type": mime_type,
        "message": f"Successfully saved user's image as artifact '{artifact_name}'"
    }


# Create FunctionTools for agent use
save_image_tool = FunctionTool(func=save_image_artifact)
load_image_tool = FunctionTool(func=load_image_artifact)
save_bytes_tool = FunctionTool(func=save_image_bytes_artifact)  # @deprecated
list_artifacts_tool = FunctionTool(func=list_image_artifacts)
save_user_image_tool = FunctionTool(func=save_user_image_as_artifact)  # @deprecated
save_text_tool = FunctionTool(func=save_text_artifact)
load_text_tool = FunctionTool(func=load_text_artifact)
