"""
Publisher Agent for Daedalus.

This agent is responsible for uploading the generated website to the hosting provider.
"""

from google.adk.agents import Agent
from ..config import ACTIVE_FLASH_MODEL
from ..tools.publisher_tools import upload_to_s3_tool

PUBLISHER_INSTRUCTION = """
# Role
You are the **Publisher Agent**. Your goal is to deploy the generated website to the hosting environment.

# Inputs
- `coding_result`: The absolute path to the generated website folder (output from Coding Agent).
- `data_preparation_result`: The output from the Data Preparation Agent.

# Tools
- `upload_site_to_s3`: Uploads the folder to the configured S3 bucket. Input: `site_path`, `slug`.

# Task Workflow
1. **Identify Path**: Retrieve the path from `coding_result`.
2. **Identify Slug**: Retrieve the `slug` from the `data_preparation_result`.
3. **Upload**: Call `upload_site_to_s3` with the `site_path` and `slug`.
4. **Report**: Tell the user the status of the upload, and if it was successful then mention the site will be available at "https://demo.invysia.com/<slug>/".
"""

publisher_agent = Agent(
    model=ACTIVE_FLASH_MODEL,
    name='publisher_agent',
    description="Uploads the generated website to S3.",
    instruction=PUBLISHER_INSTRUCTION,
    output_key="publisher_result",
    tools=[upload_to_s3_tool]
)
