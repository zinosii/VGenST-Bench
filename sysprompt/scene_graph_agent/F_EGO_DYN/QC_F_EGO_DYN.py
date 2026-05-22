TASK_DEFINITION = """
The ability to determine the final number of objects inside an opaque container by tracking a sequential series of add (insert) and remove (extract) actions performed by an agent, whose cumulative net effect cannot be read from any single frame.
"""

TASK_RULES = """
1) Reasoning Goal: Determine how many objects are inside the opaque container at the end of the video. The model must arithmetically track each add (+1) and remove (-1) action across the full sequence, since the container interior is never visible.
2) The scene must be a realistic Figural Scale environment (small-scale, graspable objects on a surface).
3) Scene Setup:
   - One opaque, wide, open-top container (no lid) placed at the center of the anchor surface. The container must be wide enough for objects to be easily dropped in from above. The container starts EMPTY.
   - Exactly <<INITIAL_SURFACE_COUNT>> identical small objects are visible on the surface beside the container at the start.
4) The camera is fixed in a first-person eye-level perspective (Ego-view), facing the front face of the container. The camera must not move. At this eye-level angle, the container walls fully block any view of the interior — the inside is NEVER visible.
5) All objects must be visually IDENTICAL (same color, shape, and size). This eliminates identity-based shortcuts and forces pure quantity tracking.
6) The container starts EMPTY. No establishment sequence is needed — actions begin immediately from the first frame.
7) Action types:
   - ADD: Agent picks one object from the surface and places it inside the container. The object visibly disappears into the container.
   - REMOVE: Agent reaches into the container and places one object onto the surface. The object visibly appears from the container.
8) Each action must be brief and unambiguous. The agent must fully retract the hand and pause between each action to visually separate events.
9) The container must remain opaque throughout — interior must NEVER be visible at any point.
"""

TASK_GUIDELINES = """
1. First Frame Specification:
   - Camera: Fixed eye-level ego view, facing the FRONT FACE of the container. The surface and container are seen from the front, not from above.
   - Container: Opaque, centered on the surface. Walls tall enough that the interior is completely invisible from this eye-level angle — only the front exterior face is visible. The open top is out of frame or too high to see into.
   - Objects: Exactly <<INITIAL_SURFACE_COUNT>> identical objects visible on the surface beside the container. Actions begin immediately.

2. Container Requirements:
   - Must be opaque, wide, and open-top (no lid) with walls tall enough that the interior is COMPLETELY HIDDEN from the eye-level front-facing camera.
   - The opening must be wide enough for objects to be easily dropped in from above.
   - Good: Wide cardboard box, wide metal tin, wide wooden chest, wide ceramic canister — opaque, open-top, wide opening facing UP, walls tall enough that the inside cannot be seen from eye-level.
   - Bad: Shallow bowl, short tray, transparent container, narrow-necked bottle, lidded container, or any container whose interior is visible from the front at eye-level.

3. Object Design (CRITICAL):
   - All objects on the surface must be visually IDENTICAL — same color, shape, and size.

4. Action Execution:
   - ADD: Hand picks one object from the surface -> moves it over the container -> drops it in (object disappears).
   - REMOVE: Hand reaches into container -> lifts one object out -> places it on the surface (object appears).
   - Each action must be visually unambiguous. No simultaneous actions.
   - Full hand retraction and brief pause between each action to separate events clearly.
"""

FIXED_CONTEXT = """You must strictly adhere to these constraints:
Spatial Scale: Figural Space (Small scale, graspable objects).
Scene Dynamics: Dynamic Scene (Actions by an agent).
Perspective: Ego View (First-person perspective).
Task Logic: Quantity Change Tracking."""

CREATIVE_PROCESS = """
The user will provide only a Theme (e.g., "Office Desk", "Kitchen Counter"). You must:
1) Imagine a Setting: Visualize a flat surface (Anchor) fitting that theme.
2) Select a Container: Choose an opaque container fitting the theme (e.g., a wooden box on a desk, a cookie tin on a kitchen counter). ADD "Tall" to the description.
3) Select Objects: Choose ONE type of small, identical object fitting the theme (e.g., paper clips, marbles, coins, candy pieces). ALL objects must look exactly alike.
4) USE FIXED SEQUENCE (from EXTRA_PARAMS_CYCLE — do NOT change):
   - Action sequence: <<ACTION_SEQUENCE>>
   - Final count inside: <<FINAL_INSIDE>>
5) Execute each action in <<ACTION_SEQUENCE>> immediately from the first frame, clearly and sequentially.
"""

OUTPUT_SCHEMA = """{{
  "scene_meta": {{
    "spatial_scale": "Figural",
    "scene_dynamics": "Dynamic",
    "perspective": "Ego",
    "task_type": "Quantity_Change_Tracking",
    "theme": "User's Theme"
  }},
  "objects": [
    {{
      "id": "obj_anchor",
      "label": "Theme-appropriate Surface (e.g., Wooden Desk)",
      "role": "anchor",
      "attributes": {{ "color": "..." }}
    }},
    {{
      "id": "obj_container",
      "label": "Theme-appropriate Tall Opaque Container (e.g., Tall Wooden Box)",
      "role": "container",
      "attributes": {{
        "material": "Opaque (e.g., Wood, Metal, Cardboard)",
        "initial_state": "Empty"
      }}
    }},
    {{
      "id": "obj_items",
      "label": "Theme-appropriate Identical Objects (e.g., Red Marbles)",
      "role": "countable_items",
      "attributes": {{
        "appearance": "All identical in color and shape",
        "initial_location": "<<INITIAL_SURFACE_COUNT>> identical objects visible on the surface beside the container"
      }}
    }}
  ],
  "temporal_flow": {{
    "initial_setup": {{
      "description": "The [container] sits empty on the [surface]. <<INITIAL_SURFACE_COUNT>> identical [objects] are visible on the surface beside it. Actions begin immediately."
    }},
    "action_sequence": [
      {{
        "step": 1,
        "action": "ADD or REMOVE",
        "action_description": "The hand picks one [object] from the surface and drops it into the [container]. / The hand reaches into the [container] and places one [object] onto the surface."
      }}
    ]
  }},
  "camera_movement": {{
    "type": "Fixed Angle",
    "trajectory": "Eye-level, facing the front face of the container. Static."
  }},
  "ground_truth": {{
    "initial_inside_count": 0,
    "action_sequence": <<ACTION_SEQUENCE>>,
    "final_inside_count": <<FINAL_INSIDE>>,
    "reasoning": "Started with 0 inside (<<INITIAL_SURFACE_COUNT>> objects on surface). Applied <<ACTION_SEQUENCE>>. Final count: <<FINAL_INSIDE>>."
  }}
}}"""

EXTRA_PARAMS_CYCLE = [
    {
        "ACTION_SEQUENCE": ["ADD", "ADD"],
        "FINAL_INSIDE": 2,
        "INITIAL_SURFACE_COUNT": 2,
    },
    {
        "ACTION_SEQUENCE": ["ADD", "ADD", "ADD"],
        "FINAL_INSIDE": 3,
        "INITIAL_SURFACE_COUNT": 3,
    },
    {
        "ACTION_SEQUENCE": ["ADD", "ADD", "REMOVE"],
        "FINAL_INSIDE": 1,
        "INITIAL_SURFACE_COUNT": 3,
    },
    {
        "ACTION_SEQUENCE": ["ADD", "REMOVE"],
        "FINAL_INSIDE": 0,
        "INITIAL_SURFACE_COUNT": 1,
    },
]
