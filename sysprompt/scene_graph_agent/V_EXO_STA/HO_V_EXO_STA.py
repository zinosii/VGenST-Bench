TASK_DEFINITION = """
The ability to determine the vertical height ordering of three objects placed at different elevations within a space, by observing a vertically tilting camera that reveals each object sequentially.
"""

TASK_RULES = """
1) Reasoning Goal: Determine the height ordering (lowest to highest) of three objects observed during a vertical camera tilt. The model must identify height ranking of the objects.
2) The scene must be a realistic Vista Scale environment (single room scale).
3) All objects must remain absolutely stationary throughout the entire video. Only the camera is allowed to move.
4) Camera Setup:
   - The camera is at a FIXED position. It does NOT translate — only tilts up or down.
   - The camera tilts in the <<TILT_DIR>> direction (Bottom-to-Top or Top-to-Bottom).
5) Object Placement:
   - Object A: On the <<FIRST_LEVEL>> (seen first).
   - Object B: On the <<SECOND_LEVEL>> (seen second).
   - Object C: On the <<THIRD_LEVEL>> (seen third).
6) Distractor: One additional distractor object is placed at the <<DISTRACTOR_LEVEL>> level, right next to the object already at that level. The distractor must be visually distinct from all other objects but occupies the same height level as its neighbor.
7) Each object (including distractor) must be a small, visually distinct item — clearly recognizable at each height level.
"""

TASK_GUIDELINES = """
1. First Frame Specification:
   - Camera: Fixed position, looking at the <<FIRST_LEVEL>> level.
   - Visible: Object A is centered in frame at the <<FIRST_LEVEL>> level.
   - Hidden: Objects B and C are out of frame (above or below).
   - Distractor: If the distractor is at this level, it is visible side by side with Object A.

2. Camera Movement Sequence:
   - Phase 1 (Object A): Camera holds on Object A at <<FIRST_LEVEL>>. If the distractor is at this level, both Object A and the distractor are visible side by side.
   - Phase 2 (Tilt to Object B): Camera tilts <<TILT_DIR>>. Object A exits frame. Object B at <<SECOND_LEVEL>> comes into view and becomes centered.
   - Phase 3 (Tilt to Object C): Camera continues tilting <<TILT_DIR>>. Object B exits frame. Object C at <<THIRD_LEVEL>> comes into view and becomes centered. If the distractor is at this level, both Object C and the distractor are visible side by side. Video ends.

3. Object Design:
   - Each object must be a small, everyday item appropriate to the theme.
   - Objects should look natural at their height level (e.g., shoes on floor, mug on table, book on shelf).

4. Scene Stability:
   - All objects completely frozen. No movement, animation, or visual changes.
   - Camera ONLY tilts vertically — no horizontal pan, no zoom, no translation.

5. Height Level Clarity:
   - The three levels must be clearly separated in vertical space.
"""

FIXED_CONTEXT = """You must strictly adhere to these constraints:
Spatial Scale: Vista Scale (single room with vertical levels).
Scene Dynamics: Static Scene (Objects do not move; only the camera moves).
Perspective: Exo View (Fixed camera position, looking at objects on different height levels).
Task Logic: Height Ordering."""

CREATIVE_PROCESS = """
The user will provide a Theme (e.g., "Living Room", "Office", "Kitchen"). You must:
1) Design the Room: A room fitting the theme with clearly defined lowest, middle, and highest levels.
2) Design Three Distinct Objects, one for each level:
   - lowest object: Something naturally found on the lowest level for this theme.
   - middle object: Something naturally found on a middle level for this theme.
   - highest object: Something naturally found on a highest level for this theme.
3) Design a Distractor Object: Placed at the <<DISTRACTOR_LEVEL>> level, right next to the object already there. Must be visually distinct from all other objects.
4) Assign objects to the reveal order based on <<TILT_DIR>>:
   - Bottom-to-Top: lowest object first, middle object second, highest object third.
   - Top-to-Bottom: highest object first, middle object second, lowest object third.
5) Determine Ground Truth: Height ranking from lowest to highest.
"""

OUTPUT_SCHEMA = """{{
  "scene_meta": {{
    "spatial_scale": "Vista",
    "scene_dynamics": "Static",
    "perspective": "Exo",
    "task_type": "Height_Ordering",
    "theme": "User's Theme"
  }},
  "objects": [
    {{
      "id": "obj_lowest",
      "label": "Theme-appropriate lowest Object (e.g., Red Sneakers)",
      "role": "lowest_object",
      "attributes": {{ "color": "...", "type": "...", "height_level": "lowest", "placement": "..." }}
    }},
    {{
      "id": "obj_middle",
      "label": "Theme-appropriate middle Object (e.g., Blue Ceramic Mug)",
      "role": "middle_object",
      "attributes": {{ "color": "...", "type": "...", "height_level": "middle", "placement": "..." }}
    }},
    {{
      "id": "obj_highest",
      "label": "Theme-appropriate highest Object (e.g., Green Potted Plant)",
      "role": "highest_object",
      "attributes": {{ "color": "...", "type": "...", "height_level": "highest", "placement": "..." }}
    }},
    {{
      "id": "obj_distractor",
      "label": "Theme-appropriate Distractor Object (e.g., Yellow Pencil Cup)",
      "role": "distractor",
      "attributes": {{ "color": "...", "type": "...", "height_level": "<<DISTRACTOR_LEVEL>>", "placement": "..." }}
    }}
  ],
  "camera_movement": {{
    "type": "Fixed-Position Vertical Tilt",
    "tilt_direction": "<<TILT_DIR>>",
    "trajectory": "Hold on <<FIRST_LEVEL>> object → tilt <<TILT_DIR>> to <<SECOND_LEVEL>> object → continue tilt to <<THIRD_LEVEL>> object."
  }},
  "ground_truth": {{
    "height_ranking_low_to_high": ["obj_lowest", "obj_middle", "obj_highest"],
    "lowest_object": "obj_lowest",
    "middle_object": "obj_middle",
    "highest_object": "obj_highest",
    "tilt_direction": "<<TILT_DIR>>"
  }}
}}"""

EXTRA_PARAMS_CYCLE = [
    {"TILT_DIR": "Bottom-to-Top", "FIRST_LEVEL": "lowest", "SECOND_LEVEL": "middle", "THIRD_LEVEL": "highest", "DISTRACTOR_LEVEL": "lowest"},
    {"TILT_DIR": "Bottom-to-Top", "FIRST_LEVEL": "lowest", "SECOND_LEVEL": "middle", "THIRD_LEVEL": "highest", "DISTRACTOR_LEVEL": "highest"},
    {"TILT_DIR": "Top-to-Bottom", "FIRST_LEVEL": "highest", "SECOND_LEVEL": "middle", "THIRD_LEVEL": "lowest", "DISTRACTOR_LEVEL": "highest"},
    {"TILT_DIR": "Top-to-Bottom", "FIRST_LEVEL": "highest", "SECOND_LEVEL": "middle", "THIRD_LEVEL": "lowest", "DISTRACTOR_LEVEL": "lowest"},
]
