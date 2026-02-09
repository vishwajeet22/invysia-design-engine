"""
Daedalus Design Pipeline - Autonomous agent pipeline
"""
import vertexai
from google.adk.agents.llm_agent import Agent
from google.adk.agents import SequentialAgent

from .subagents.data_preparation_agent import data_preparation_agent
from .subagents.information_architect_agent import information_architect_agent
from .subagents.navigation_manager_agent import navigation_manager_agent
from .subagents.base_wireframe_agent import base_wireframe_agent
from .subagents.storyboard_agent import storyboard_agent
from .subagents.asset_manager_agent import asset_manager_agent
from .subagents.coding_agent import coding_agent
from .subagents.publisher_agent import publisher_agent

vertexai.init(
    project="project-1023a394-e63c-4912-8ed",
    location="global"
)

daedalus_pipeline = SequentialAgent(
    name="DaedalusDesignPipeline",
    sub_agents=[data_preparation_agent, information_architect_agent, navigation_manager_agent, base_wireframe_agent, storyboard_agent, asset_manager_agent, coding_agent, publisher_agent],
    description="End-to-end design pipeline.",
)

root_agent = daedalus_pipeline
