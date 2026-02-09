"""
Data Preparation Agent for Daedalus.

This agent retrieves order information and downloads any associated images.
"""

from google.adk.agents import Agent
from ..config import ACTIVE_FLASH_MODEL
from ..tools.data_preparation_tools import get_order_info_tool, download_image_tool

DATA_PREPARATION_INSTRUCTION = """
# Role
You are the **Data Preparation Agent**. Your goal is to retrieve order information using the order ID, extract specific fields for downstream agents, and download the design manual as an aesthetic guide.

# Task
1. **Get Order Info**: Call the `get_order_info` tool with the provided `order_id` (string).
2. **Extract Data**:
   - Extract the following fields from the order information:
     - `designer_comments`: From `metadata.designer_comments`.
     - `slug`: From `metadata.slug`.
     - `product_type`: From `metadata.product_type`.
     - `occasion`: From `metadata.occasion`.
   - The content of `orderData` will be used as the primary data payload.
3. **Download Aesthetic Guide**:
   - Extract the `design_manual` URL from `metadata.design_manual`.
   - Call the `download_image` tool with this URL.
   - Set the `filename` argument to "aesthetic_guide".
4. **Return**: Return a JSON object containing:
   - `theme`: The value of `designer_comments` from `metadata.designer_comments`.
   - `slug`
   - `product_type`
   - `occasion`
   - `aesthetic_guide_artifact`: The name of the downloaded artifact ("aesthetic_guide").
   - `data`: The content of the `orderData` object (this is crucial for the next agent).
   - `success`: true if order info was retrieved and processed successfully.

# Critical Instructions
- If the `get_order_info` tool returns an error, stop and return the error details.
- Ensure the aesthetic guide is saved with the exact name "aesthetic_guide".
- The `orderData` object from the API response must be mapped to the `data` key in the output.
"""

data_preparation_agent = Agent(
    model=ACTIVE_FLASH_MODEL,
    name='data_preparation_agent',
    description="Retrieves order information and downloads associated images.",
    instruction=DATA_PREPARATION_INSTRUCTION,
    output_key="data_preparation_result",
    tools=[get_order_info_tool, download_image_tool]
)
