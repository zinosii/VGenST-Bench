TASK_DEFINITION = """
The ability to integrate visual cues from a complex ego-centric navigation path to estimate the direction back to the starting position within a static single-room environment.
"""

TASK_RULES = """
1) Reasoning Goal: Perform 'Path Integration'. After the camera navigates through an L-shaped trajectory (including a Right/Left turn), the model must identify the direction back to the Start Point relative to its final heading, expressed in clock position format (e.g., "8 o'clock").
2) The scene must be a realistic Vista Scale environment (single room or corridor scale).
3) All objects must remain absolutely stationary throughout the entire video. Only the camera is allowed to move.
4) Visual Cues: The room must have at least two distinct landmarks (large, high-contrast objects) to serve as spatial anchors. The Start Point itself is not marked.
5) ROOM STRUCTURE RULE (CRITICAL): The environment MUST have a physical L-shaped spatial structure (corridor that turns). Open rectangular rooms or any space where all walls are simultaneously visible from the start are PROHIBITED.
6) First Frame Rule: The first frame MUST show only Landmark 1 ahead. Landmark 2 is not visible from the starting position because the corridor turns.
7) Turn direction and ground truth are determined by EXTRA_PARAMS_CYCLE. Do NOT change the turn direction.
"""

TASK_GUIDELINES = """
1. First Frame Specification:
   - Camera: Eye-level first-person view, facing straight down Seg 1 toward Landmark 1.
   - Landmark 1 is clearly visible in the distance ahead (large and distinct).
   - The corridor turns <<TURN_DIRECTION>> ahead, but Seg 2 is not yet visible from this position.
   - Landmark 2 is not visible because the corridor has not turned yet.

2. Camera Movement — Walking Simulation:
   - All movement must simulate natural human walking: eye-level height, slight forward/vertical sway, no drone-like smoothness.
   - Single continuous shot with no cuts, jump cuts, or teleportation.

3. Trajectory Path (L-Shape):
   (a) Seg 1: Walk forward toward Landmark 1 along the first corridor.
   (b) Turn: At the corner, execute a smooth <<TURN_DIRECTION>> rotation. The transition must be visually clear — the viewer must perceive the change of direction.
   (c) Seg 2: Walk forward in the new direction toward Landmark 2.
   (d) Stop: Come to a complete stop. Final position is the endpoint.
   - The final position must be significantly displaced from the start, making path integration non-trivial.

4. Landmark Design:
   - Landmark 1: At the far end of Seg 1. Clearly visible from the Start Position.
   - Landmark 2: At the far end of Seg 2. Becomes visible only after the turn.
   - Both landmarks must be large, high-contrast, and immediately recognizable (e.g., a bright red sofa, a large blue painting).
   - When turning, ensure visual overlap between the pre-turn and post-turn views so the model can stitch the space together.
"""

FIXED_CONTEXT = """You must strictly adhere to these constraints:
Spatial Scale: Vista Scale (single room scale).
Scene Dynamics: Static Scene (Objects do not move; only the camera moves).
Perspective: Ego View (First-person perspective).
Task Logic: Direction Estimation."""

CREATIVE_PROCESS = """
The user will provide only a Theme (e.g., "Museum Hallway", "living room"). You must:
1) Design the Room Structure FIRST:
   - The environment MUST have a physical L-shaped structure.
   - Explicitly decide the architectural layout: which direction is Seg 1, where the corner wall is, and which direction is Seg 2.

2) Place Landmarks based on the structure:
   - Landmark 1: At the far end of Seg 1 (on the North wall). Visible from Start.
   - Landmark 2: At the far end of Seg 2 (on the <<SEG2_DIRECTION>> wall). Not visible from Start because the corridor turns.

3) Design the Trajectory (The "L-Shape" Path):
   - Seg 1: Move forward towards Landmark 1 (North wall).
   - Turn: Rotate 90 degrees <<TURN_DIRECTION>> at the corner.
   - Seg 2: Move forward towards Landmark 2 (<<SEG2_DIRECTION>> wall).
   - Stop: Final position.

4) Calculate Ground Truth:
   - This scene graph MUST use a <<TURN_DIRECTION>> turn (North -> <<SEG2_DIRECTION>>).
   - The Start Point is located at <<TURN_DIRECTION_RESULT>> relative to the final heading.
   - DO NOT change the turn direction. It is fixed for this generation.
"""

OUTPUT_SCHEMA = """{{
  "scene_meta": {{
    "spatial_scale": "Vista",
    "scene_dynamics": "Static",
    "perspective": "Ego",
    "task_type": "Direction_Estimation",
    "theme": "User's Theme"
  }},
  "objects": [
    {{
      "id": "landmark_1",
      "label": "Theme-appropriate Object (e.g., Sofa)",
      "role": "landmark_1 (Visible in Seg 1)",
      "attributes": {{ "color": "...", "position": "Far end of North wall" }}
    }},
    {{
      "id": "landmark_2",
      "label": "Theme-appropriate Object (e.g., Chair)",
      "role": "landmark_2 (Visible in Seg 2)",
      "attributes": {{ "color": "...", "position": "Far end of <<SEG2_DIRECTION>> wall" }}
    }},
  ],
  "camera_movement": {{
    "type": "Person Walking Simulation",
    "trajectory": "Start facing North at origin. Walk forward along Seg 1 towards Landmark 1 (North wall). Execute a smooth <<TURN_DIRECTION>> turn at the corner. Walk forward along Seg 2 towards Landmark 2 (<<SEG2_DIRECTION>> wall). Stop."
  }},
  "ground_truth": {{
    "turn_direction": "<<TURN_DIRECTION>>",
    "relative_direction_to_start": "<<TURN_DIRECTION_RESULT>>",
    "reasoning": "The camera started facing North, moved forward (Seg 1), then turned <<TURN_DIRECTION>> to face <<SEG2_DIRECTION>> (Seg 2). Final facing direction is <<SEG2_DIRECTION>>. The Start Point is now <<START_RELATIVE>> relative to the final position. <<REASONING_DETAIL>>"
  }}
}}"""

EXTRA_PARAMS_CYCLE = [
    {
        "TURN_DIRECTION": "Right",
        "SEG2_DIRECTION": "East",
        "TURN_DIRECTION_RESULT": "Back-Right (approx 4-5 o'clock)",
        "START_RELATIVE": "South-West",
        "REASONING_DETAIL": "Relative to an East-facing heading, South is Right (3 o'clock) and West is Back (6 o'clock). Therefore, South-West is Back-Right, approx 4-5 o'clock."
    },
    {
        "TURN_DIRECTION": "Left",
        "SEG2_DIRECTION": "West",
        "TURN_DIRECTION_RESULT": "Back-Left (approx 7-8 o'clock)",
        "START_RELATIVE": "South-East",
        "REASONING_DETAIL": "Relative to a West-facing heading, South is Left (9 o'clock) and East is Back (6 o'clock). Therefore, South-East is Back-Left, approx 7-8 o'clock."
    }
]
