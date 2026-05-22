TASK_DEFINITION = """
The ability to deduce the spatial position of Landmark 3 relative to Landmark 1 by combining two sequential camera movements: (1) a crane-up that reveals Landmark 2's position relative to Landmark 1, and (2) a directional flight that travels from the Landmark 1-2 area to Landmark 3. The model must compose both movements to infer the final spatial relationship.
"""

TASK_RULES = """
1) Reasoning Goal: Determine where Landmark 2 and Landmark 3 are located relative to Landmark 1.
2) Parameter Selection (YOU decide randomly per scene graph.
   - L2_APPEAR, {N, NE, E, SE, S, SW, W, NW}  (8 compass directions on the top-down map; N = up on screen, E = right, S = down, W = left)
   - DRIFT_DIR, {N, NE, E, SE, S, SW, W, NW}  (8 compass directions; the direction the camera flies on the top-down map)
   - L3_DIRECTION = DRIFT_DIR (because the camera flies in DRIFT_DIR from the L1 area and stops at L3, so L3 ends up in that same compass direction from L1).
   Pick L2_APPEAR and DRIFT_DIR independently.
3) Environment: A large-scale environmental setting viewed from a perfect 90-degree top-down bird's-eye perspective. All landmarks are seen as rooftop shapes from directly above.
4) All landmarks remain absolutely stationary throughout the entire video. Only the camera moves.
5) Camera Sequence:
   - Image (Anchor Frame): Tight close-up bird's-eye view of Landmark 1 rooftop, centered.
   - Phase 1 (Crane Up): Camera ascends rapidly. The view widens. Landmark 2 appears to the L2_APPEAR of Landmark 1. Both are visible simultaneously from above, separated by significant distance.
   - Phase 2 (Fly to L3): Camera physically flies in the DRIFT_DIR direction at high speed. Landmark 1 and 2 exit frame. After traveling a very long distance (much farther than L1-L2), Landmark 3 appears and becomes centered in tight close-up.
6) Landmark Placement:
   - Landmark 1: Camera's starting position (center of anchor frame).
   - Landmark 2: To the L2_APPEAR of Landmark 1 (revealed during crane-up).
   - Landmark 3: Reached by flying DRIFT_DIR from the L1-L2 area (much farther away).
7) Each landmark must be a large, visually distinct environmental-scale structure — clearly recognizable as a rooftop from directly above.
8) Landmarks must be spread far apart — NOT adjacent.
9) CRITICAL DISTANCE: L3 must be MUCH farther from L1 than L2 is. L2 is relatively nearby (visible during crane-up), but L3 requires a long camera flight to reach — it is in a completely different part of the environment.
10) Ground Truth: L3 is to the L3_DIRECTION of L1 (derived from DRIFT_DIR per rule 2).
"""

TASK_GUIDELINES = """
1. First Frame (Anchor Image):
   - Camera: Perfect 90-degree top-down bird's-eye view, low altitude, tight close-up.
   - Visible: Landmark 1 rooftop is centered and fills the frame. Surrounding terrain visible.
   - Hidden: Landmarks 2 and 3 are not visible (too far away at this altitude).

2. Phase 1 (Crane Up):
   - Camera ascends rapidly, maintaining top-down angle.
   - The field of view widens as altitude increases.
   - Landmark 2 rooftop enters the frame to the L2_APPEAR side of Landmark 1 (the value you chose).
   - Both landmarks are visible simultaneously with significant distance between them.
   - This phase establishes the L1-L2 spatial relationship.

3. Phase 2 (Fly to L3):
   - Camera physically flies in the DRIFT_DIR compass direction you chose (N=up, NE=upper-right, E=right, SE=lower-right, S=down, SW=lower-left, W=left, NW=upper-left — all on the top-down map) at high speed.
   - Landmark 1 and Landmark 2 exit the frame.
   - After traveling a very long distance across terrain (much farther than L1-L2 distance), Landmark 3 rooftop enters frame.
   - Camera descends to tight close-up on Landmark 3. Video ends.

4. Landmark Design:
   - Each landmark must be a LARGE environmental-scale structure with a distinctive rooftop shape visible from directly above.
   - Must be clearly distinguishable from top-down perspective — unique color, shape, and footprint.

5. Spatial Clarity:
   - All landmarks seen ONLY from directly above (strict top-down, no tilting).
   - Camera movements must be fast to cover large distances.
   - Terrain between landmarks should be theme-appropriate (city grid, forest, desert, etc.).
"""

FIXED_CONTEXT = """You must strictly adhere to these constraints:
Spatial Scale: Environmental Scale (large-scale terrain viewed from bird's-eye).
Scene Dynamics: Static Scene (all landmarks stationary; only the camera moves).
Perspective: Exo View (perfect 90-degree top-down bird's-eye throughout).
Task Logic: Landmark Spatial Composition (combine crane-up reveal + directional flight to infer spatial relationship)."""

CREATIVE_PROCESS = """
The user will provide a Theme (e.g., "Downtown Skyline", "Desert Mesa"). You must:
1) RANDOMLY pick L2_APPEAR, {N, NE, E, SE, S, SW, W, NW} and DRIFT_DIR, {N, NE, E, SE, S, SW, W, NW}. Use the theme as inspiration and make sure your choices VARY across different themes.
2) L3_DIRECTION equals DRIFT_DIR (the camera flies in DRIFT_DIR and lands on L3, so L3 sits in that compass direction relative to L1).
3) Design the Environment: A large-scale setting fitting the theme, viewed from directly above.
4) Design Three Distinct Landmarks with unique rooftop shapes/colors:
   - Landmark 1: Camera starts here (anchor frame close-up).
   - Landmark 2: Appears to the L2_APPEAR direction during crane-up.
   - Landmark 3: Reached by flying DRIFT_DIR (much farther from L1 than L2 is).
5) Output the chosen L2_APPEAR, DRIFT_DIR, and the derived L3_DIRECTION in the ground_truth section of the JSON.
"""

OUTPUT_SCHEMA = """{{
  "scene_meta": {{
    "spatial_scale": "Environmental",
    "scene_dynamics": "Static",
    "perspective": "Exo",
    "task_type": "Landmark_Spatial_Composition",
    "theme": "User's Theme"
  }},
  "objects": [
    {{
      "id": "obj_landmark_1",
      "label": "Theme-appropriate Landmark 1 (e.g., Red Brick Clock Tower)",
      "role": "landmark_start",
      "attributes": {{ "color": "...", "type": "...", "rooftop_shape": "..." }}
    }},
    {{
      "id": "obj_landmark_2",
      "label": "Theme-appropriate Landmark 2 (e.g., White Domed Concert Hall)",
      "role": "landmark_craneup",
      "attributes": {{ "color": "...", "type": "...", "rooftop_shape": "...", "position_relative_to_L1": "(your chosen L2_APPEAR: N|NE|E|SE|S|SW|W|NW)" }}
    }},
    {{
      "id": "obj_landmark_3",
      "label": "Theme-appropriate Landmark 3 (e.g., Green Glass Skyscraper)",
      "role": "landmark_flight",
      "attributes": {{ "color": "...", "type": "...", "rooftop_shape": "..." }}
    }}
  ],
  "camera_movement": {{
    "type": "Crane-Up then Directional Flight",
    "L2_appear_direction": "(your chosen L2_APPEAR: N|NE|E|SE|S|SW|W|NW)",
    "drift_direction": "(your chosen DRIFT_DIR: N|NE|E|SE|S|SW|W|NW)",
    "trajectory": "Tight close-up on L1 rooftop → rapid crane up (L2 appears to the chosen L2_APPEAR) → rapid flight in the chosen DRIFT_DIR across vast terrain → tight close-up on L3 rooftop."
  }},
  "ground_truth": {{
    "L2_relative_to_L1": "(your chosen L2_APPEAR)",
    "drift_direction": "(your chosen DRIFT_DIR)",
    "L3_relative_to_L1": "(derived L3_DIRECTION: N|NE|E|SE|S|SW|W|NW, same as DRIFT_DIR)",
    "reasoning": "Crane-up revealed L2 to the (L2_APPEAR) of L1. Camera then flew (DRIFT_DIR) a very long distance to reach L3. Therefore L3 is to the (L3_DIRECTION) of L1."
  }}
}}"""
