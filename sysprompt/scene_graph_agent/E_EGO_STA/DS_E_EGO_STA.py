TASK_DEFINITION = """
The ability to interpret directional signage (text and arrows) within a large-scale environment to deduce the destination corresponding to the ego-agent's current heading.
"""

TASK_RULES = """
1) Reasoning Goal: Given directional signage with text and arrows, the model must determine which destination (if any) the ego-agent is heading toward based on the direction they are actually walking.
2) The scene must be a realistic Environmental Scale environment (e.g., Airport Terminal, Subway Station, Hospital Corridor). The entire space implies a massive network beyond the visible frame.
3) Key Element: Static Directional Signage.
   - The sign must contain at least two distinct entries, each with a clear Text (Destination) and an Arrow (Direction).
   - Example: "Terminal 2 [straight arrow]" and "Baggage Claim [left arrow]".
   - Text must be large and legible. Arrow directions must be unambiguous.
4) All objects must remain absolutely stationary throughout the entire video. Only the camera is allowed to move.
5) Agent Path: The camera moves continuously in the direction specified by <<AGENT_PATH>> (Straight, Left, or Right). This path is fixed — do NOT change it.
6) Reasoning Logic: Map the 2D arrow on the sign to the 3D ego-motion.
   - If sign says "Exit [right arrow]" and camera goes Straight, the agent is NOT heading to Exit.
   - The agent's actual path may match one of the sign entries, or may match none (heading somewhere not indicated).
"""

TASK_GUIDELINES = """
1. First Frame Specification:
   - Camera: Eye-level first-person, standing at one end of a long corridor, facing toward the sign in the distance.
   - Visible: The directional sign is visible ahead, mounted on the wall or hanging from the ceiling.
   - The corridor should convey Environmental Scale: high ceilings, long perspective lines, large open space.
   - No motion yet — this frame establishes the scene and direction of travel.

2. Environmental Design:
   - Use architectural cues to suggest a large-scale facility: high ceilings, long perspective lines, wide corridors, specific textures (terrazzo floors, polished tiles, industrial ceiling panels).
   - The scale must imply that the destination is far beyond the visible frame.

3. Signage Placement & Design:
   - Mount the sign naturally: hanging from the ceiling or mounted on the wall at head-height.
   - Do NOT fill the frame with the sign — it should be an environmental cue, not a close-up poster.
   - Arrow direction must be visually unambiguous (no diagonal arrows).

4. Camera Motion (The Walk):
   - Phase 1: Camera starts at the far end of the corridor, sign visible ahead.
   - Phase 2: Sign passes overhead or to the side.
   - Phase 3: Camera continues walking in the <<AGENT_PATH>> direction (Straight, Left, or Right), proving the actual heading.
   - Smooth, steady movement throughout. No shaking, no cuts.
"""

FIXED_CONTEXT = """You must strictly adhere to these constraints:
Spatial Scale: Environmental Scale (Airport Terminal, Subway Station, Hospital Corridor).
Scene Dynamics: Static Scene (objects do not move; only the camera moves).
Perspective: Ego View (first-person perspective).
Task Logic: Directional Signage Grounding."""

CREATIVE_PROCESS = """
The user will provide a Location Theme (e.g., "International Airport"). You must:
1) Design the Corridor: A long, wide path fitting the theme. Convey Environmental Scale.
2) Create a Sign with exactly two entries using two DIFFERENT directions:
   - Entry A: Destination A (e.g., "Gates 1-50"), Direction A (e.g., Straight)
   - Entry B: Destination B (e.g., "Baggage Claim"), Direction B (e.g., Right)
   - Choose any two directions from {Straight, Left, Right}. The third direction is unmarked.
3) AGENT PATH (FIXED): The agent MUST walk in the <<AGENT_PATH>> direction. Do NOT change it.
   - If <<AGENT_PATH>> matches Direction A -> agent is heading to Destination A.
   - If <<AGENT_PATH>> matches Direction B -> agent is heading to Destination B.
   - If <<AGENT_PATH>> matches neither -> agent is heading somewhere not indicated on the sign.
4) Design the walk: camera approaches sign -> reads it -> continues in <<AGENT_PATH>> direction.
5) Formulate Ground Truth: Based on <<AGENT_PATH>>, which destination (if any) is the agent heading toward?
"""

OUTPUT_SCHEMA = """{{
  "scene_meta": {{
    "spatial_scale": "Environmental",
    "scene_dynamics": "Static",
    "perspective": "Ego",
    "task_type": "Directional_Signage_Grounding",
    "theme": "User's Theme"
  }},
  "objects": [
    {{
      "id": "obj_sign",
      "label": "Directional Sign (e.g., Overhead Terminal Sign)",
      "role": "signage",
      "attributes": {{
        "entry_A": {{ "text": "[DESTINATION_A]", "arrow": "[DIRECTION_A]" }},
        "entry_B": {{ "text": "[DESTINATION_B]", "arrow": "[DIRECTION_B]" }},
        "placement": "... (e.g., hanging from ceiling, mounted on wall) ...",
      }}
    }}
  ],
  "camera_movement": {{
    "type": "Person Walking Simulation",
    "trajectory": "Start at far end of corridor facing sign → walk toward sign (sign becomes readable) → sign passes overhead/side → continue walking in <<AGENT_PATH>> direction."
  }},
  "ground_truth": {{
    "agent_heading": "<<AGENT_PATH>>",
    "destination": "[MATCHING_DESTINATION if <<AGENT_PATH>> matches a sign entry, or 'Not indicated on sign' if no match]",
    "reasoning": "The agent walked [<<AGENT_PATH>>], which matches the arrow for '[MATCHING_DESTINATION]' on the sign."
  }}
}}"""

EXTRA_PARAMS_CYCLE = [
    {"AGENT_PATH": "Straight"},
    {"AGENT_PATH": "Left"},
    {"AGENT_PATH": "Right"},
]
