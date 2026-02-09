"""
Base Wireframe Agent for generating wireframes for individual slides.

This agent iteratively generates HTML/CSS wireframes for each slide
identified by the information_architect_agent, stores them as artifacts,
and returns a list of artifact names.
"""

from typing import AsyncGenerator, Dict, Any, List
from typing_extensions import override

from google.adk.agents import Agent
from google.adk.tools import FunctionTool, AgentTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from ..config import ACTIVE_FLASH_MODEL


# --- Tool Definitions ---

async def save_wireframe_artifact(
    filename: str,
    html_content: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Save the generated HTML wireframe as an artifact.

    Args:
        filename: Name of the file (e.g., 'slide_1_wireframe.html')
        html_content: The HTML content string
        tool_context: The ToolContext for artifact operations

    Returns:
        Dict containing success status and artifact details
    """
    # Ensure filename ends with .html
    if not filename.endswith('.html'):
        filename += '.html'

    # Convert string to bytes
    try:
        html_bytes = html_content.encode('utf-8')
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to encode HTML content: {str(e)}"
        }

    # Create the artifact part
    try:
        html_part = types.Part.from_bytes(data=html_bytes, mime_type='text/html')
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create artifact part: {str(e)}"
        }

    # Save as artifact
    try:
        version = await tool_context.save_artifact(filename=filename, artifact=html_part)
        return {
            "success": True,
            "file_path": filename,
            "version": version,
            "message": f"Successfully saved wireframe as '{filename}'"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to save artifact: {str(e)}"
        }


save_wireframe_tool = FunctionTool(func=save_wireframe_artifact)


# --- Wireframe LLM Agent Instructions ---

WIREFRAME_LLM_INSTRUCTION = """
You are the WireframeLlmAgent, responsible for creating a low-fidelity wireframe for a SINGLE SLIDE using HTML and CSS.
You do not use images or other media. You only use text and basic shapes.

# Input
You will receive data for a single slide via the state key `temp:current_slide_data`. This data represents:
- `slide_id`: The identifier for this slide
- `slide_number`: The number of this slide (1-indexed)
- `datasets`: List of dataset keys assigned to this slide

# Design Constraints

1. **Low Fidelity**: Use gray placeholders for images (gray divs with text like "Image Placeholder"). Do not use real images.
2. **Layout**: Be creative with layout. Use CSS flexbox or grid for styling. Focus on typography and whitespace.
3. **Mobile First**: Design for mobile screens (1080x1920 reference). The wireframe should fit within this aspect ratio.
4. **Single Slide**: Focus ONLY on the content for the current slide. Do NOT generate navigation flows or multiple pages.

# Output Format

1. Generate a complete HTML document with embedded CSS.
2. The HTML should be self-contained and viewable in a browser.
3. Use the `save_wireframe_artifact` tool to save the HTML with the filename provided in `temp:current_artifact_name`.
4. Return a confirmation that the wireframe was saved successfully.

# Example HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wireframe - Slide 1</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f5f5f5; }
        .slide { 
            min-height: 100vh; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center;
            padding: 20px;
        }
        .placeholder {
            background: #ddd;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="slide">
        <!-- Slide content here -->
    </div>
</body>
</html>
```
"""


# --- Wireframe LLM Agent Definition ---

wireframe_llm_agent = Agent(
    model=ACTIVE_FLASH_MODEL,
    name='wireframe_llm_agent',
    description="Generates HTML/CSS wireframe for a single slide.",
    instruction=WIREFRAME_LLM_INSTRUCTION,
    tools=[save_wireframe_tool],
    output_key="temp:wireframe_result"
)

# --- Orchestrator Agent ---

base_wireframe_agent = Agent(
    model=ACTIVE_FLASH_MODEL,
    name='base_wireframe_agent',
    description="Generates HTML/CSS wireframe for the slides generated by information_architect_agent.",
    instruction="""
    **Role:** Wireframe Generation Agent

    **Primary Objective:** To generate wireframes for each slide, utilizing the 'wireframe_llm_agent'.

    **Core Tasks:**

    1.  **Retrieve Slide Mappings and Data:**
        * Access the session state and retrieve the slide mappings under the key 'slide_mapping_result'

    2.  **Process Each Slide:** Iterate through each slide defined in the slide_mapping_result. For each slide, keep track of the current slide number (starting from 1).
        Set the slide data under the key 'temp:current_slide_data'.
        Call 'wireframe_llm_agent' to get the generated wireframe saved as artifact. Store its name from state key 'temp:current_artifact_name', maintaining the order corresponding to the slide number.

    3.  **Maintain Slide Order:** Ensure that the generated artifact names for the wireframes are stored in an ordered list based on the slide number they correspond to.

    4.  **Return Ordered List of Slide Wireframes:** Once all slides in the input have been processed and a wireframe has been generated and stored for each, return an ordered list (formatted in markdown as bullet list with active links) containing all the artifact names. This list represents the sequence of wireframes for the presentation, in the order of the slides.

    """,
    tools=[AgentTool(agent=wireframe_llm_agent)],
    output_key="wireframe_result"
)
