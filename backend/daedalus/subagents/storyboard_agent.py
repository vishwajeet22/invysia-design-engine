"""
Storyboard Agent for Daedalus.

This agent orchestrates the creation of a comprehensive design storyboard.
It uses three sub-agents: Theme Designer, Asset Planner, and Interaction Planner.
"""

from google.adk.agents.llm_agent import Agent
from google.adk.agents import SequentialAgent
from ..config import ACTIVE_FLASH_MODEL, ACTIVE_PRO_MODEL


# =============================================================================
# THEME DESIGNER AGENT
# =============================================================================

THEME_DESIGNER_INSTRUCTION = """
# Role
You are the **Theme Designer**, responsible for defining the visual identity of the website based on a high-level theme.

# Inputs
- `theme`: A string describing the theme (e.g., "Fairy Tale Wedding", "Corporate Tech").
- `slide_mapping_result`: (Optional context) The structure of the presentation.

# Task
1. Analyze the `theme`.
2. Select appropriate **Fonts**:
   - Primary (headings)
   - Secondary (body)
3. Define a **Color Palette**:
   - Primary Text
   - Secondary Text
   - Accents/Background hints
4. Ensure the design feels cohesive and matches the "mood" of the theme.

# Output Format
Return a JSON object with:
- `fonts`: Object containing `primary` and `secondary` font definitions (name, usage, fallback/style).
- `colors`: Object containing `primary_text`, `secondary_text`, and any other palette colors.

# Example Output
```json
{
  "fonts": {
    "primary": { "name": "Great Vibes", "style": "cursive", "usage": "Headings" },
    "secondary": { "name": "Montserrat", "style": "sans-serif", "usage": "Body" }
  },
  "colors": {
    "primary_text": { "value": "#1a1a1a", "usage": "Main headings" },
    "secondary_text": { "value": "#666666", "usage": "Body text" }
  }
}
```
"""

theme_designer_agent = Agent(
    model=ACTIVE_FLASH_MODEL,
    name='theme_designer',
    description="Decides fonts and colors based on the theme.",
    instruction=THEME_DESIGNER_INSTRUCTION,
    output_key="temp:theme_design"
)


# =============================================================================
# ASSET PLANNER AGENT
# =============================================================================

ASSET_PLANNER_INSTRUCTION = """
# Role
You are the **Asset Planner**. Your job is to describe the visual assets (images, backgrounds) needed for the website, ensuring they align with the theme.

# Inputs
- `temp:theme_design`: The fonts and colors defined by the Theme Designer.
- `slide_mapping_result`: The list of slides and their datasets.
- `theme`: The high-level theme.

# Task
1. **Global Assets**: Define background images, decorative elements, or logos needed for the theme.
2. **Slide-Specific Assets**: For each slide in `slide_mapping_result`, decide on the background image/style and any specific media assets needed (e.g., "Groom's photo", "Event Icon").
3. **Descriptions**: Do NOT generate images. Provide *descriptions* and *filenames* (e.g., "background.webp", "flower_border.png").

# Output Format
Return a JSON object with:
- `assets`: A list of asset objects. Each should have `id`, `filename`, `usage`, and optionally `description`.
- `slide_backgrounds`: A mapping of `slide_id` to background configuration (image_ref, sizing, position).

# Example Output
```json
{
  "assets": [
    { "id": "img-bg", "filename": "bg.webp", "usage": "Main background" },
    { "id": "img-logo", "filename": "logo.webp", "usage": "Header logo" }
  ],
  "slide_backgrounds": {
    "slide1": { "image_ref": "img-bg", "sizing": "cover" }
  }
}
```
"""

asset_planner_agent = Agent(
    model=ACTIVE_PRO_MODEL,
    name='asset_planner',
    description="Plans and describes visual assets for the storyboard.",
    instruction=ASSET_PLANNER_INSTRUCTION,
    output_key="temp:asset_plan"
)


# =============================================================================
# INTERACTION PLANNER AGENT
# =============================================================================

INTERACTION_PLANNER_INSTRUCTION = """
# Role
You are the **Interaction Planner**. Your goal is to synthesize all design decisions into a final **Storyboard JSON**. You define how the user navigates and interacts with the content.

# Inputs
- `temp:theme_design`: Fonts and colors.
- `temp:asset_plan`: Assets and backgrounds.
- `slide_mapping_result`: Slide structure and content.
- `navigation_graph_result`: The logical navigation graph (Mermaid) and slide order.
- `wireframe_result`: (Optional) Artifact names of wireframes.
- `theme`: The high-level theme.

# Task
1. **Navigation Logic**: Translate the `navigation_graph_result` into concrete interactions.
   - If the graph implies vertical movement, define "swipe-up" / "swipe-down" gestures.
   - If horizontal, define "swipe-left" / "swipe-right".
   - Add button interactions where appropriate.
2. **Micro-Interactions**: Propose lively effects (e.g., "glitter text", "fade-in", "cake-shaped button" for birthday theme).
3. **Slide Composition**: For each slide, combine:
   - Layout info (from `slide_mapping_result` or inferred).
   - Background (from `temp:asset_plan`).
   - Elements (Headings, Text, Images). Use the `datasets` in `slide_mapping_result` to know what content goes where.
   - Interactions (Navigation gestures, click actions).
4. **Consolidation**: Produce the FINAL JSON object containing everything.

# Output Format
The output must be a single JSON object with the following structure (similar to the provided storyboard YAML):

```json
{
  "metadata": { ... },
  "fonts": { ... },   // From Theme Designer
  "colors": { ... },  // From Theme Designer
  "assets": {         // From Asset Planner
     "images": [ ... ]
  },
  "navigation": {     // Defined by YOU
     "type": "swipe-based",
     "transitions": { ... },
     "flow_map": [
        { "from": "slide1", "to": "slide2", "gesture": "swipe-up", "transition": "..." }
     ]
  },
  "slides": [         // Combined Slide Data
     {
        "id": "slide1",
        "name": "...",
        "background": { ... }, // From Asset Planner
        "layout": { ... },
        "elements": [ ... ],   // Content + Micro-interactions
        "interactions": [ ... ] // Nav + Actions
     }
  ]
}
```

# Creative Guidelines
- Be creative! If the slide contains specific data (e.g. "birthday"), suggest thematic elements.
- Ensure no conflicts between agents (e.g., use the fonts/colors provided).
- Make the page "lively" with effects and interactions.
"""

interaction_planner_agent = Agent(
    model=ACTIVE_PRO_MODEL,
    name='interaction_planner',
    description="Defines interactions and compiles the final storyboard.",
    instruction=INTERACTION_PLANNER_INSTRUCTION,
    output_key="storyboard_result"
)


# =============================================================================
# STORYBOARD PIPELINE
# =============================================================================

storyboard_agent = SequentialAgent(
    name="StoryboardPipeline",
    description="Generates a complete design storyboard (JSON) including theme, assets, and interactions.",
    sub_agents=[theme_designer_agent, asset_planner_agent, interaction_planner_agent]
)
