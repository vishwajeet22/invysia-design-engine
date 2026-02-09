"""
Tools for the AssetManager agent.
"""

import time
import os
import json
import asyncio
import tempfile
from pathlib import Path
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types, Client
from ..config import google_genai_client
from .image_tools import remove_background, convert_to_webp

# Valid aspect ratios supported by Gemini image generation API
VALID_ASPECT_RATIOS = {'1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9'}

async def generate_image(
    prompt: str,
    aspect_ratio: str,
    model: str,
    artifact_filename: str,
    tool_context: ToolContext
) -> dict:
    """
    Generates an image using the specified model.

    Args:
        prompt: The image generation prompt.
        aspect_ratio: The desired aspect ratio. Must be one of: '1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', or '21:9'.
        model: The model to use (e.g. "gemini-3-pro-image-preview").
        artifact_filename: The filename to save the artifact as.
        tool_context: The tool context.

    Returns:
        Dict containing success status and artifact name.
    """
    # Validate aspect ratio
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        return {
            "success": False,
            "error": f"Invalid aspect_ratio '{aspect_ratio}'. Must be one of: {', '.join(sorted(VALID_ASPECT_RATIOS))}"
        }

    client = google_genai_client

    # Configure image settings based on model
    if model == "gemini-3-pro-image-preview":
        image_config = types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size="1K",
        )
    else:
        # For gemini-2.5-flash-image and other models
        image_config = types.ImageConfig(
            aspect_ratio=aspect_ratio,
        )

    config = types.GenerateContentConfig(
        image_config=image_config,
        http_options=types.HttpOptions(timeout=90000)  # 90 seconds in milliseconds
    )

    max_retries = 3
    last_error = None

    print(f"Generating image with prompt: {prompt[:50]}... using model {model}, aspect_ratio: {aspect_ratio}")

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=[prompt],
                config=config,
            )

            image_data = None
            if hasattr(response, 'candidates') and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_data = part.inline_data.data
                        break

            if image_data:
                # Save to artifact store
                # mime_type might be in part.inline_data.mime_type, defaulting to png
                mime_type = "image/png"

                image_part = types.Part.from_bytes(data=image_data, mime_type=mime_type)
                await tool_context.save_artifact(filename=artifact_filename, artifact=image_part)

                return {
                    "success": True,
                    "artifact_name": artifact_filename,
                    "message": "Image generated and saved to artifacts."
                }
            else:
                print(f"Attempt {attempt + 1}: No image data found in response.")

        except Exception as e:
            last_error = str(e)
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2)  # Wait before retry

    return {
        "success": False,
        "error": f"Failed to generate image after {max_retries} attempts. Last error: {last_error}"
    }

async def analyze_background_color_palette(
    tool_context: ToolContext
) -> dict:
    """
    Analyzes the background.png artifact to identify the color palette and suggest a contrasting one.

    Args:
        tool_context: The tool context.

    Returns:
        Dict containing the analysis text.
    """
    client = google_genai_client

    # Load background.png
    bg_artifact = await tool_context.load_artifact(filename="background.png")
    if not bg_artifact:
        return {"success": False, "error": "background.png artifact not found."}

    # Prepare prompt
    prompt = """
    Analyze this background image and identify the color palette used in it.
    Then, define a color palette that is consistent with the theme in the background but also contrasts the colors of the background for better visibility.
    For example, if the background is pinkish, you need to define a palette that uses tinges of red, orange, or darker pinks.
    Return the result as a text description.
    """

    try:
        # Assuming bg_artifact can be passed directly or needs to be converted
        # types.Part object usually works with generate_content if it has inline_data

        # We need to construct a Part if not already one compatible with the client
        # The tool_context.load_artifact returns a google.genai.types.Part usually

        contents = [prompt, bg_artifact]

        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=contents
        )

        if response.text:
            return {
                "success": True,
                "analysis": response.text
            }
        else:
            return {"success": False, "error": "No text response from model."}

    except Exception as e:
        return {"success": False, "error": str(e)}

async def generate_morphed_image_helper(
    client: Client,
    original_image_path: Path,
    prompt: str,
    output_filename: str,
    tool_context: ToolContext,
    target_dir: Path
):
    """Helper to generate a single morphed image."""
    max_retries = 3
    delay = 2

    try:
        # Read image file
        image_bytes = original_image_path.read_bytes()
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png") # Assuming PNG or compatible

        # Configure for editing (assuming gemini-2.5-flash-image supports it via standard generate_content)
        # We pass the image and the prompt

        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=[prompt, image_part],
                    # No specific config needed for simple generation, but maybe aspect ratio?
                    # Since we want to preserve structure, we usually don't force aspect ratio if it matches input
                    # But the API might require it. Let's assume defaults work for editing.
                )

                image_data = None
                if hasattr(response, 'candidates') and response.candidates:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            image_data = part.inline_data.data
                            break

                if image_data:
                    # Save artifact
                    out_part = types.Part.from_bytes(data=image_data, mime_type="image/png")
                    await tool_context.save_artifact(filename=output_filename, artifact=out_part)

                    # Save to local system
                    local_path = target_dir / output_filename
                    local_path.write_bytes(image_data)

                    return {"filename": output_filename, "status": "success"}

                print(f"Attempt {attempt+1} for {output_filename}: No image data.")
            except Exception as e:
                print(f"Attempt {attempt+1} for {output_filename} failed: {e}")

            await asyncio.sleep(delay)
            delay *= 2 # Exponential backoff

        return {"filename": output_filename, "status": "failed", "error": "Max retries exceeded"}

    except Exception as e:
        return {"filename": output_filename, "status": "failed", "error": str(e)}

async def morph_images(
    base_assets_path: str,
    tool_context: ToolContext
) -> dict:
    """
    Generates morphed versions of images listed in assets.json.

    Args:
        base_assets_path: Path containing assets.json and source images.
        tool_context: ToolContext.

    Returns:
        Dict with results.
    """
    client = google_genai_client

    base_path = Path(base_assets_path)
    assets_json_path = base_path / "assets.json"

    if not assets_json_path.exists():
        return {"success": False, "error": f"assets.json not found at {base_assets_path}"}

    try:
        with open(assets_json_path, 'r') as f:
            assets_data = json.load(f)

        # Extract image paths
        # Handle both {"assets": [{"path":...}]} and [{"path":...}] or list of strings
        image_files = []
        if isinstance(assets_data, dict) and "assets" in assets_data:
            items = assets_data["assets"]
        elif isinstance(assets_data, list):
            items = assets_data
        else:
            items = []

        for item in items:
            if isinstance(item, str):
                image_files.append(item)
            elif isinstance(item, dict) and "path" in item:
                image_files.append(item["path"])
            elif isinstance(item, dict) and "filename" in item:
                image_files.append(item["filename"])

        if not image_files:
            return {"success": True, "message": "No images found in assets.json to process."}

        # Load morph prompt
        prompt_artifact = await tool_context.load_artifact(filename="asset_morph_prompt.txt")
        if not prompt_artifact or not prompt_artifact.text:
             # Try falling back to bytes decode if text is missing
             if prompt_artifact and prompt_artifact.inline_data:
                 morph_prompt = prompt_artifact.inline_data.data.decode('utf-8')
             else:
                 return {"success": False, "error": "asset_morph_prompt.txt not found or empty."}
        else:
             morph_prompt = prompt_artifact.text

        # Prepare target directory
        target_dir = base_path / "assets_output"
        target_dir.mkdir(parents=True, exist_ok=True)

        tasks = []
        for img_rel_path in image_files:
            original_path = base_path / img_rel_path
            if not original_path.exists():
                print(f"Warning: Source image {original_path} does not exist.")
                continue

            # Determine output filename
            stem = original_path.stem
            suffix = original_path.suffix
            output_filename = f"{stem}_morphed{suffix}"

            tasks.append(
                generate_morphed_image_helper(
                    client,
                    original_path,
                    morph_prompt,
                    output_filename,
                    tool_context,
                    target_dir
                )
            )

        results = await asyncio.gather(*tasks)

        return {
            "success": True,
            "results": results
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

async def save_all_assets(
    base_assets_path: str,
    tool_context: ToolContext
) -> dict:
    """
    Saves all generated assets (prompts and images) to a local folder.

    Args:
        base_assets_path: The base path where the output folder will be created.
        tool_context: The tool context.

    Returns:
        Dict containing paths to saved files.
    """
    try:
        # Create a new output folder at base path
        target_dir = Path(base_assets_path) / "assets_output"
        target_dir.mkdir(parents=True, exist_ok=True)

        saved_files = {}

        # List of artifacts to save
        artifacts_to_save = [
            "design_manual_prompt.txt",
            "design_manual.png",
            "background_prompt.txt",
            "background.png",
            "asset_morph_prompt.txt"
        ]

        for artifact_name in artifacts_to_save:
            artifact_part = await tool_context.load_artifact(filename=artifact_name)
            if artifact_part:
                file_path = target_dir / artifact_name

                if artifact_part.inline_data:
                    # It's binary data (image) or text saved as bytes
                    file_path.write_bytes(artifact_part.inline_data.data)
                    saved_files[artifact_name] = str(file_path)
                elif artifact_part.text:
                    # It's text
                    file_path.write_text(artifact_part.text, encoding='utf-8')
                    saved_files[artifact_name] = str(file_path)
                else:
                    # Fallback for text in bytes
                     try:
                        # Try getting bytes if text is None but it is text artifact
                        # types.Part doesn't always have .text set if loaded from storage
                        # But for safe measure let's check blob
                        if hasattr(artifact_part, 'blob') and artifact_part.blob:
                             file_path.write_bytes(artifact_part.blob.data)
                             saved_files[artifact_name] = str(file_path)
                     except:
                        print(f"Warning: Could not extract data for {artifact_name}")

            else:
                # asset_morph_prompt might not exist if steps were skipped, just warn
                print(f"Warning: Artifact {artifact_name} not found.")

        return {
            "success": True,
            "saved_files": saved_files
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

async def remove_background_artifact(
    artifact_filename: str,
    tool_context: ToolContext
) -> dict:
    """
    Removes the background from an image artifact.

    Args:
        artifact_filename: The name of the artifact to process.
        tool_context: The tool context.

    Returns:
        Dict containing success status and new artifact name.
    """
    try:
        artifact = await tool_context.load_artifact(filename=artifact_filename)
        if not artifact:
            return {"success": False, "error": f"Artifact {artifact_filename} not found."}

        # Determine input data
        if artifact.inline_data:
            data = artifact.inline_data.data
        elif hasattr(artifact, 'blob') and artifact.blob:
            data = artifact.blob.data
        else:
            return {"success": False, "error": f"Artifact {artifact_filename} has no data."}

        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / artifact_filename
            input_path.write_bytes(data)

            # Process
            output_path = remove_background(input_path=input_path)

            # Read output
            output_data = output_path.read_bytes()
            new_artifact_name = output_path.name

            # Save back to artifacts
            # Mime type should be png for transparency
            new_part = types.Part.from_bytes(data=output_data, mime_type="image/png")
            await tool_context.save_artifact(filename=new_artifact_name, artifact=new_part)

            return {
                "success": True,
                "artifact_name": new_artifact_name,
                "message": "Background removed successfully."
            }

    except Exception as e:
        return {"success": False, "error": str(e)}

async def convert_to_webp_artifact(
    artifact_filename: str,
    tool_context: ToolContext
) -> dict:
    """
    Converts an image artifact to WebP format.

    Args:
        artifact_filename: The name of the artifact to process.
        tool_context: The tool context.

    Returns:
        Dict containing success status and new artifact name.
    """
    try:
        artifact = await tool_context.load_artifact(filename=artifact_filename)
        if not artifact:
            return {"success": False, "error": f"Artifact {artifact_filename} not found."}

        # Determine input data
        if artifact.inline_data:
            data = artifact.inline_data.data
        elif hasattr(artifact, 'blob') and artifact.blob:
            data = artifact.blob.data
        else:
            return {"success": False, "error": f"Artifact {artifact_filename} has no data."}

        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / artifact_filename
            input_path.write_bytes(data)

            # Process
            output_path = convert_to_webp(input_path=input_path)

            # Read output
            output_data = output_path.read_bytes()
            new_artifact_name = output_path.name

            # Save back to artifacts
            new_part = types.Part.from_bytes(data=output_data, mime_type="image/webp")
            await tool_context.save_artifact(filename=new_artifact_name, artifact=new_part)

            return {
                "success": True,
                "artifact_name": new_artifact_name,
                "message": "Converted to WebP successfully."
            }

    except Exception as e:
        return {"success": False, "error": str(e)}

# Create tool instances
generate_image_tool = FunctionTool(func=generate_image)
analyze_background_color_palette_tool = FunctionTool(func=analyze_background_color_palette)
morph_images_tool = FunctionTool(func=morph_images)
save_assets_tool = FunctionTool(func=save_all_assets)
remove_background_tool = FunctionTool(func=remove_background_artifact)
convert_to_webp_tool = FunctionTool(func=convert_to_webp_artifact)
