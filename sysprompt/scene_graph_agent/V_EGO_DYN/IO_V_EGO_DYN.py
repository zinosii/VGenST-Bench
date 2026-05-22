TASK_DEFINITION = """
The ability to identify which specific object a third-party agent physically interacted with (picked up and relocated), observed from a stationary first-person viewpoint among multiple visible distractor objects.
"""

TASK_RULES = """
1) Reasoning Goal: Identify which ONE object (out of three) the agent picked up and moved to a different location.
2) The scene must be a realistic Vista Scale environment (single room).
3) The ego viewpoint is a STATIONARY first-person observer (seated or standing at one fixed location). The camera does NOT move throughout the video.
4) The scene contains exactly THREE distinct objects arranged in a row on a primary surface (e.g., coffee table, desk, shelf), at positions Left, Center, and Right, all clearly visible in the frame.
5) A secondary destination surface (e.g., side shelf, armchair, counter) must also be visible in the frame, distinct from the primary surface.
6) A single third-party agent enters the frame from the <<AGENT_ENTRY>> side (off-screen).
7) The agent picks up EXACTLY ONE target object located at the <<TARGET_POSITION>> position on the primary surface, carries it to the secondary destination, and places it down there.
8) The other two objects on the primary surface are distractors — they remain stationary and untouched throughout the video. The model must correctly exclude them.
"""

TASK_GUIDELINES = """
1. First Frame Specification:
   - Camera: Eye-level first-person view from a stationary observer (seated on sofa, standing in doorway, etc.).
   - Primary surface with three distinct objects in a row (Left, Center, Right) clearly visible in the foreground.
   - Secondary destination surface visible elsewhere in the frame (not overlapping with primary surface).
   - No agent visible in the first frame yet.

2. Object Design:
   - All three objects must be visually distinct: different colors AND different categories (e.g., red mug, blue book, green apple).
   - All three must be small, one-hand graspable items (mug, book, vase, remote, candle, apple, bottle, picture frame, etc.).
   - Objects placed with clear spatial separation so Left/Center/Right is unambiguous.
   - Distractors should be theme-appropriate and plausibly belong on the primary surface, not obviously "out of place".

3. Camera Movement:
   - Completely static throughout the entire video.
   - No pan, tilt, zoom, dolly, or head movement.
   - Height, angle, and framing remain identical from first frame to last.

4. Temporal Flow:
   Phase 1 — Establishment:
     - Static scene. Three objects visible on primary surface. 
     - No agent present. Room is still.
   
   Phase 2 — Agent Entry:
     - A single agent enters the frame from the <<AGENT_ENTRY>> side.
     - Agent walks toward the primary surface.
     - Agent's full body or upper body visible; face not required (side/back view preferred for generation stability).
   
   Phase 3 — Pick-up:
     - Agent reaches the primary surface and picks up the object at the <<TARGET_POSITION>> position.
     - The other two objects remain completely undisturbed at their positions.
     - Pick-up motion clearly visible, no occlusion of the target object at the moment of contact.
   
   Phase 4 — Transport & Place:
     - Agent carries the target object to the secondary destination surface.
     - Placement clearly visible.
   
5. Agent Design:
   - Single human or robot agent.
"""

FIXED_CONTEXT = """You must strictly adhere to these constraints:
Spatial Scale: Vista Scale (single room).
Scene Dynamics: Dynamic Scene (third-party agent walks and manipulates an 
object; ego observer is stationary).
Perspective: Ego View (first-person stationary observer).
Task Logic: Interacted_Object Identification."""

CREATIVE_PROCESS = """
The user will provide only a Theme (e.g., "Living Room", "Kitchen Counter"). You must:
1) Imagine a Setting: A room fitting the theme, with the ego observer stationed at a natural viewpoint (seated on furniture, standing in a doorway, etc.).
2) Choose a Primary Surface visible in the foreground (coffee table, dining table, desk, kitchen island, counter, etc.) where 3 objects will be arranged in a row.
3) Choose a Secondary Destination Surface also visible in the frame, spatially distinct from the primary surface.
4) Place 3 Objects at Left, Center, Right positions on the primary surface:
   - All must be small, one-hand graspable items.
   - All must be visually distinct (different color AND different category).
   - All must be theme-appropriate.
5) Confirm the agent's entry direction <<AGENT_ENTRY>> is clear (off-screen space available on that side).
"""

OUTPUT_SCHEMA = """{{
  "scene_meta": {{
    "spatial_scale": "Vista",
    "scene_dynamics": "Dynamic",
    "perspective": "Ego",
    "task_type": "Interacted_Object_Identification",
    "theme": "User's Theme"
  }},
  "objects": [
    {{
      "id": "obj_agent",
      "label": "Theme-appropriate Agent (e.g., Human)",
      "role": "agent",
      "attributes": {{ "appearance": "..." }}
    }},
    {{
      "id": "obj_primary_surface",
      "label": "Theme-appropriate Surface (e.g., Wooden Table)",
      "role": "primary_surface",
      "attributes": {{ "color": "..." }}
    }},
    {{
      "id": "obj_destination_surface",
      "label": "Theme-appropriate Surface (e.g., Bookshelf Middle Shelf)",
      "role": "destination_surface",
      "attributes": {{ "color": "..." }}
    }},
    {{
      "id": "obj_Left",
      "label": "Small graspable object (e.g., Red Ceramic Mug)",
      "position": "Left",
      "role": "target | distractor",
      "attributes": {{ "color": "..." }}
    }},
    {{
      "id": "obj_Center",
      "label": "Small graspable object (e.g., Blue Hardcover Book)",
      "position": "Center",
      "role": "target | distractor",
      "attributes": {{ "color": "..." }}
    }},
    {{
      "id": "obj_Right",
      "label": "Small graspable object (e.g., Green Apple)",
      "position": "Right",
      "role": "target | distractor",
      "attributes": {{ "color": "..." }}
    }}
  ],
  "temporal_flow": {{
    "initial_setup": {{
      "description": "Stationary first-person view of the primary surface with three distinct objects (Left, Center, Right) clearly visible. Secondary destination surface also visible. No agent present."
    }},
    "action_sequence": [
      {{
        "step": 1,
        "action_description": "Agent enters from <<AGENT_ENTRY>>, walks to primary surface."
      }},
      {{
        "step": 2,
        "action_description": "Agent picks up object at <<TARGET_POSITION>>."
      }},
      {{
        "step": 3,
        "action_description": "Agent carries the object to the secondary destination surface and places it down."
      }}
    ]
  }},
  "camera_movement": {{
    "type": "Fixed Angle",
    "trajectory": "No movement. Fixed eye-level viewpoint from stationary observer."
  }},
  "ground_truth": {{
    "target_object_id": "obj_<<TARGET_POSITION>>",
    "target_position": "<<TARGET_POSITION>>",
    "agent_entry_direction": "<<AGENT_ENTRY>>",
    "destination": "Description of destination surface"
  }}
}}"""


EXTRA_PARAMS_CYCLE = [
    {"AGENT_ENTRY": "Left",  "TARGET_POSITION": "Left"},
    {"AGENT_ENTRY": "Left",  "TARGET_POSITION": "Center"},
    {"AGENT_ENTRY": "Left",  "TARGET_POSITION": "Right"},
    {"AGENT_ENTRY": "Right", "TARGET_POSITION": "Left"},
    {"AGENT_ENTRY": "Right", "TARGET_POSITION": "Center"},
    {"AGENT_ENTRY": "Right", "TARGET_POSITION": "Right"},
]
