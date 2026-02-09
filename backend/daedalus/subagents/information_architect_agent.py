"""
Information Architect Agent for Daedalus.

This agent generates slide-dataset mapping from structured JSON input.
It also extracts metadata from the input and stores it in session state.
"""

import json
from typing import Optional
from google.adk.agents.llm_agent import Agent
from google.adk.agents.callback_context import CallbackContext
from ..config import ACTIVE_FLASH_MODEL
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types


def extract_metadata_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Before model callback to extract metadata from input and store in session state.
    
    Expected input format:
    {
        "theme": "...",           # metadata - stored in state["theme"]
        "due_date": "...",        # metadata - stored in state["due_date"]
        "data": { ... }           # actual structured data for processing
    }
    
    Any key other than "data" is treated as metadata and stored in session state.
    The "data" key content is extracted and passed to the model for processing.
    """
    state = callback_context.state
    
    # Get the last user message from llm_request contents
    if not llm_request.contents:
        return None
    
    last_content = llm_request.contents[-1]
    if last_content.role != 'user' or not last_content.parts:
        return None
    
    user_text = None
    for part in last_content.parts:
        if hasattr(part, 'text') and part.text:
            user_text = part.text
            break
    
    if not user_text:
        return None
    
    try:
        input_json = json.loads(user_text)
    except json.JSONDecodeError:
        # Not valid JSON, let the agent handle the raw input
        return None
    
    if not isinstance(input_json, dict):
        return None
    
    # Extract metadata (all keys except "data") and store in state
    data_content = None
    for key, value in input_json.items():
        if key == "data":
            data_content = value
        else:
            # Store metadata in session state for downstream agents
            state[key] = value
    
    # If "data" key exists, modify the last user message to contain only the data
    if data_content is not None:
        # Replace the last content's text with just the data JSON
        modified_part = types.Part.from_text(text=json.dumps(data_content))
        llm_request.contents[-1] = types.Content(
            role="user",
            parts=[modified_part]
        )
    
    # Return None to proceed with the (potentially modified) request
    return None


INFORMATION_ARCHITECT_INSTRUCTION = """
# Role
You are the **Information Architect**, an AI agent responsible for designing the slide-dataset mapping for a data-driven presentation. Your goal is to analyze structured JSON input and create an optimal slide mapping that distributes datasets across slides. After generating the slide-dataset mapping, transfer back to the root agent.

# Input Format
You will receive a structured JSON object where:
- Each key is a dataset identifier (e.g., "dataset1", "hero_section", "gallery")
- Each value is either a JSON object or a JSON array
- You must work ONLY with the provided data - do NOT invent or assume any additional data

Note: Metadata (such as "theme", "due_date", etc.) has already been extracted and stored in session state before this instruction runs. You only receive the actual data to process.

# Core Logic & Rules

### 1. Slide Grouping & Assignment
* **Capacity**: The total number of slides must be **less than 10**.
* **Coverage**: Every dataset from the input must appear in at least one slide.
* **Distribution**: Distribute datasets evenly. A single slide can hold multiple datasets, or a single dataset (if it is a list) can span multiple slides.
* **Constraint - Fullscreen**: If an object has `"requires_fullscreen": true`, it **must** generally be on its own slide.
    * *Heterogeneous Lists*: If a list dataset contains some objects requiring fullscreen and others that don't, separate the fullscreen objects into their own slides and group the non-fullscreen objects together.

### 2. Sequencing
* **Sequence ID**: Respect the `sequence` attribute of datasets if present. Lower numbers must appear earlier in the navigation flow.
* **Ties**: Datasets with the same `sequence` number can be ordered randomly relative to each other or grouped on the same slide.
* **Randomization**: You are **stateless**. You must introduce randomization in your grouping and ordering choices (where constraints allow) so that running this task multiple times on the same input yields different valid results.

### 3. Navigation Axis Selection
You must define a **Primary Axis** (for moving between datasets) and a **Secondary Axis** (for moving within a list dataset).

* **Axis Consistency**:
    * If Primary Axis is **Vertical** (Up/Down), then Secondary Axis must be **Horizontal** (Left/Right) or Linear (Next/Prev).
    * If Primary Axis is **Horizontal** (Left/Right), then Secondary Axis must be **Vertical** (Up/Down).
    * If Primary Axis is **Linear** (Next/Previous), then Secondary Axis must be **Horizontal** (Left/Right) or Vertical (Up/Down).
    * *Constraint*: Navigation style must be consistent. You cannot mix "Up" and "Right" within the same hierarchy level.

# Output Format

Return a JSON object with:
- `slide_mappings`: A list of objects, each with:
  * `slide_id`: The slide identifier (e.g., "slide1")
  * `datasets`: List of dataset keys for this slide (e.g., ["dataset1"] or ["dataset2[0]"] or ["dataset3", "dataset4"])
- `primary_axis`: The chosen primary axis ("vertical", "horizontal", or "linear")
- `secondary_axis`: The chosen secondary axis ("vertical", "horizontal", or "linear")
- `success`: true if successful
- `error`: null if successful, error message otherwise

# Example
*Input*: `{"dataset1": {...}, "dataset2": [{...}, {...}, {...}], "dataset3": {...}}`
*Output*:
```json
{
  "slide_mappings": [
    {"slide_id": "slide1", "datasets": ["dataset1"]},
    {"slide_id": "slide2", "datasets": ["dataset2[0]"]},
    {"slide_id": "slide3", "datasets": ["dataset2[1]"]},
    {"slide_id": "slide4", "datasets": ["dataset2[2]"]},
    {"slide_id": "slide5", "datasets": ["dataset3"]}
  ],
  "primary_axis": "vertical",
  "secondary_axis": "horizontal",
  "success": true,
  "error": null
}
```

# Critical Constraints
- Do NOT invent data - work only with provided input
- Do NOT use any tools - analyze the input and produce output directly
- Ensure every dataset key from input appears in the mapping
"""

information_architect_agent = Agent(
    model=ACTIVE_FLASH_MODEL,
    name='information_architect',
    description="Analyzes structured JSON data and generates slide-dataset mapping with navigation axis choices.",
    instruction=INFORMATION_ARCHITECT_INSTRUCTION,
    output_key="slide_mapping_result",
    before_model_callback=extract_metadata_callback
)
