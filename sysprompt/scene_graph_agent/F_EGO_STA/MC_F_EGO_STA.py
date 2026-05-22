TASK_DEFINITION = """
The ability to map the 'Container Identity' (seen from the front) to the 'Content Identity' (seen from the top) by integrating information visible only at a specific camera angle.
"""

TASK_RULES = """
1) Reasoning Goal: Identify which content is inside each container by cross-referencing container identity (visible from the side) with content identity (visible from above). The model must integrate information from both viewpoints.
2) The scene must be a realistic Figural Scale environment (small-scale, graspable objects on a surface).
3) All objects must remain absolutely stationary throughout the entire video. Only the camera is allowed to move.
4) Camera trajectory is determined by the EXTRA_PARAMS_CYCLE parameter for each instance:
   - 'Boom_Up': Low-angle side view -> High-angle top-down view.
     The model sees container exteriors first (establishing identity), then the camera rises to reveal contents.
   - 'Boom_Down': High-angle top-down view -> Low-angle side view.
     The model sees contents first, then the camera lowers to show only container exteriors (contents hidden).
   Both trajectories must fully cover the vertical range needed to toggle content visibility (visible ↔ occluded).
5) Exactly 3 containers, all fitting the scene theme.
   - Must be open-top, opaque, and deep enough that contents are invisible from the side view.
   - Allowed: Matte-painted boxes, metal tins, ceramic mugs, opaque jars.
   - Forbidden: Glass, transparent plastic, shallow bowls (contents visible from side).
   - Each container must be visually distinct from the others (different color or shape) to allow unambiguous identity tracking.
6) Each container holds a DIFFERENT content. Contents must be clearly distinguishable from a top-down view.
"""

TASK_GUIDELINES = """
1. First Frame Specification (depends on EXTRA_PARAMS_CYCLE):

  [Boom_Up — First Frame]
   - Camera: Table-height side view. Lens roughly level with the containers' rims.
   - Containers: All 3 visible in a row, their distinct colors/shapes clearly legible.
   - Contents: Invisible. Opaque walls fully occlude all interiors.

  [Boom_Down — First Frame]
   - Camera: ~70-90 degree overhead angle, looking straight down.
   - Containers: All 3 visible from above. Interiors fully exposed — all contents clearly identifiable.

2. Camera Trajectory — Two Options (set by EXTRA_PARAMS_CYCLE):

  [Boom_Up — The Reveal]
   - Start: Camera at table-height side view. Container exteriors are clearly visible and distinguishable. Contents are fully occluded.
   - Motion: Smoothly rise vertically while tilting the lens downward (no cuts or teleportation).
   - End: Camera at ~70-90 degree overhead angle. All container interiors are clearly visible from above.
   - Cognitive demand: Model must remember container identities from the start, then map contents revealed at the end.

  [Boom_Down — The Conceal]
   - Start: Camera at ~70-90 degree overhead angle. All container interiors are fully visible.
   - Motion: Smoothly lower vertically while tilting the lens upward (no cuts or teleportation).
   - End: Camera at table-height side view. Contents are fully occluded; only container exteriors visible.
   - Cognitive demand: Model must remember content positions from the start, then identify which container held which when the viewpoint changes.

3. Container Setup:
   - Place all 3 containers side-by-side in a row on the anchor surface.
   - Containers must differ clearly in color or shape — avoid subtle differences (e.g., Red Tin vs. Blue Box vs. Green Mug).

4. Content Design:
   - Contents must be visually distinct from a top-down perspective.
     - Good: Black Coffee vs. White Milk vs. Empty (bare bottom).
     - Good: Gold Coins vs. Red Berries vs. Green Moss.
     - Bad: Water vs. Sprite (both clear), or two similarly-colored items.
   - Solid contents should protrude slightly or use high-contrast colors against the container interior.
"""

FIXED_CONTEXT = """You must strictly adhere to these constraints:
Spatial Scale: Figural Space (Small scale, graspable objects).
Scene Dynamics: Static Scene (Objects do not move; only the camera moves).
Perspective: Ego View (First-person perspective).
Task Logic: Multi-Container Attribute Mapping."""

CREATIVE_PROCESS = """
The user will provide only a Theme (e.g., "Artist's Studio", "Breakfast Table"). You must:
1) Imagine a Setting: Visualize a small surface (Anchor) fitting that theme.
2) Select Containers: Choose 3 containers fitting the theme.
   - Assign distinct identifiers (e.g., Red/Blue/Green).
   - The container must be opaque and deep enough (e.g., a green matte box, a blue steel box). Do not use transparent containers (e.g. Glass) or shallow containers that reveal contents from the side.
3) Assign Contents: Choose 3 distinct contents.
   - Example: Liquid A, Liquid B, Empty.
   - Example: Object A, Object B, Object C.
4) CAMERA TRAJECTORY (FIXED): You MUST use <<CAMERA_TRAJECTORY>> camera movement.
  * "Boom_Up": Camera starts at low angle (ground level) and tilts/booms up to bird's eye view.
  * "Boom_Down": Camera starts at high angle (bird's eye) and tilts/booms down to ground level.
5) Construct Layout: Position the camera based on camera trajectory.
"""

OUTPUT_SCHEMA = """{{
  "scene_meta": {{
    "spatial_scale": "Figural",
    "scene_dynamics": "Static",
    "perspective": "Ego",
    "task_type": "Multi_Container_Attribute_Mapping",
    "theme": "User's Theme"
  }},
  "objects": [
    {{
      "id": "obj_anchor",
      "label": "Theme-appropriate Surface (e.g., Wooden Table)",
      "role": "anchor",
      "attributes": {{ 
        "color": "..." 
        "material": "..."
      }}
    }},
    {{
      "id": "obj_container_1",
      "label": "Theme-appropriate Container 1 (e.g., Red Vase)",
      "role": "container",
      "attributes": {{
        "content": "Black Coffee",
        "color": "...",
        "material": "..."
      }}
    }},
    {{
      "id": "obj_container_2",
      "label": "Theme-appropriate Container 2 (e.g., Blue matte Mug)",
      "role": "container",
      "attributes": {{
        "content": "White Milk",
        "color": "...",
        "material": "..."
      }}
    }},
    {{
      "id": "obj_container_3",
      "label": "Theme-appropriate Container 3 (e.g., Yellow Mug)",
      "role": "container",
      "attributes": {{
        "content": "Empty",
        "color": "...",
        "material": "..."
      }}
    }}
  ],
  "spatial_layout": [
    {{
      "subject": "obj_container_1",
      "relation": "standing_on_left_of",
      "target": "obj_anchor"
    }},
    {{
      "subject": "obj_container_2",
      "relation": "standing_on_middle_of",
      "target": "obj_anchor"
    }},
    {{
      "subject": "obj_container_3",
      "relation": "standing_on_right_of",
      "target": "obj_anchor"
    }},
  ],
  "camera_movement": {{
    "type": "<<CAMERA_TRAJECTORY>>",
    "trajectory": "low_angle_to_high_angle (if Boom_Up) or high_angle_to_low_angle (if Boom_Down)"
  }},
  "ground_truth": {{
    "mapping": {{
      "Container 1 label": "its content label",
      "Container 2 label": "its content label",
      "Container 3 label": "its content label"
    }}
  }}
}}"""

EXTRA_PARAMS_CYCLE = [
    {"CAMERA_TRAJECTORY": "Boom_Up"},
    {"CAMERA_TRAJECTORY": "Boom_Down"},
]
