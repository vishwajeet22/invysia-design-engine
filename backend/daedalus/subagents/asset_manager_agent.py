"""
Asset Manager Pipeline.

This sequential pipeline orchestrates the extraction of asset requirements,
refinement of prompts, and generation of image artifacts.
"""

from google.adk.agents import SequentialAgent

from .requirements_extractor import requirements_extractor_agent
from .asset_prompt_generator import asset_prompt_generator_agent
from .asset_generator import asset_generator_agent

asset_manager_agent = SequentialAgent(
    name="AssetManagerPipeline",
    description="Sequential pipeline to extract requirements, generate prompts, and create assets.",
    sub_agents=[
        requirements_extractor_agent,
        asset_prompt_generator_agent,
        asset_generator_agent
    ]
)
