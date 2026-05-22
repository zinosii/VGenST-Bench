TASK_DEFINITION = """
The ability to identify the dynamic change in visibility status between an Observer agent and a Target agent within a Vista environment.
The model must recognize the visibility shift ('Visible' to 'Occluded' or 'Occluded' to 'Visible') relative to the Observer's perspective, caused by the physical movement of either the Target or the Observer around a central environmental obstacle.
"""

TASK_RULES = """
1) Reasoning Goal: Accurately determine the visibility status (Visible or Occluded) of the Target from the Observer's perspective before and after a movement event.
2) The scene must be a realistic Vista Scale environment (single room scale).
3) Camera: Fixed high-angle exocentric view (CCTV-style god view) throughout. The camera does not move.
   - The camera always sees ALL three entities simultaneously — including the Target even when it is occluded from the Observer.
4) The scene must contain exactly THREE items:
   - Observer: The agent whose line of sight determines visibility status.
   - Target: The other agent involved in the visibility relationship.
   - Occluder: A large static object placed at the CENTER of the scene.
5) Spatial Layout (FIXED):
   - Occluder is ALWAYS at the CENTER of the scene.
   - Observer is on the <<OBSERVER_SIDE>> side.
   - For VISIBLE state: Target must be at a DIAGONAL position (e.g., opposite-top or opposite-bottom) so that LOS bypasses the Occluder. A direct opposite position would be blocked.
   - For OCCLUDED state: Target must be directly behind the Occluder from Observer's perspective (same horizontal axis, opposite side).
6) Movement Agent (<<MOVER>>):
   - "Target_Moves": The Target physically moves to change the visibility status. The Observer remains stationary.
   - "Observer_Moves": The Observer physically moves to change the visibility status. The Target remains stationary.
7) Visibility Transition (<<VISIBILITY_TRANSITION>>):
   - "Visible_to_Occluded": Target starts at a diagonal position (visible). <<MOVER>> moves so Target ends up directly behind Occluder (occluded).
   - "Occluded_to_Visible": Target starts directly behind Occluder (occluded). <<MOVER>> moves so Target ends up at a diagonal position (visible).
8) The state change must be total — no partial occlusion or ambiguous LOS.
9) Perspective Awareness: The camera (god view) always sees the Target. The question is about what the OBSERVER sees, not the camera.
"""

TASK_GUIDELINES = """
1. First Frame Specification (depends on <<VISIBILITY_TRANSITION>>):

  [Visible_to_Occluded — First Frame]
   - Occluder at CENTER. Observer on <<OBSERVER_SIDE>>.
   - Target at a DIAGONAL position on the opposite side (e.g., if Observer is Left, Target is Right-Top or Right-Bottom).
   - LOS from Observer to Target bypasses the Occluder diagonally — clear line of sight.
   - Initial status: Observer CAN see Target.

  [Occluded_to_Visible — First Frame]
   - Occluder at CENTER. Observer on <<OBSERVER_SIDE>>.
   - Target directly behind Occluder on the opposite side (same horizontal line as Observer through Occluder).
   - LOS is blocked by the Occluder.
   - Camera (god view) can still see Target from above.
   - Initial status: Observer CANNOT see Target.

2. Camera Setup (Fixed "God View"):
   - High-angle static exocentric camera looking down. No panning, tilting, or movement.
   - ALL three entities must be simultaneously visible in every frame.

3. Diagonal Visibility Logic (CRITICAL):
   - When Observer is on Left and Target is on Right-Top or Right-Bottom: the diagonal angle means LOS passes ABOVE or BELOW the Occluder's blocking zone → VISIBLE.
   - When Observer is on Left and Target is directly on Right-Center: the horizontal LOS passes through the Occluder → OCCLUDED.
   - The movement that changes visibility is: Target (or Observer) shifts from diagonal to direct-opposite (or vice versa).

4. Movement Design (<<MOVER>>):
   [Visible_to_Occluded]
   - If Target_Moves: Target walks from diagonal position to directly behind Occluder (center axis).
   - If Observer_Moves: Observer walks to align with Occluder-Target axis, making the previously diagonal LOS now blocked.

   [Occluded_to_Visible]
   - If Target_Moves: Target walks from directly behind Occluder to a diagonal position (off the center axis).
   - If Observer_Moves: Observer walks to a position where LOS becomes diagonal, bypassing the Occluder.

5. Action Sequence:
   - Phase 1 (Initial State): Establish the starting visibility status clearly.
   - Phase 2 (Movement): <<MOVER>> moves. The LOS changes from diagonal-clear to blocked (or vice versa).
   - Phase 3 (Final Hold): Camera holds on the final configuration.

6. Clarity Constraints:
   - Observer and Target must be visually distinct (different color outfit, shape).
   - The Occluder must be large enough to block horizontal LOS but allow diagonal LOS to bypass.
"""

FIXED_CONTEXT = """You must strictly adhere to these constraints:
Spatial Scale: Vista Scale (single room scale).
Scene Dynamics: Dynamic Scene (one agent moves).
Perspective: Exo View (fixed high-angle exocentric — CCTV-style god view).
Task Logic: Visibility Identification (Observer's line-of-sight change, NOT camera visibility).
Layout: Occluder at CENTER. Diagonal = Visible, Direct opposite = Occluded."""

CREATIVE_PROCESS = """
The user will provide only a Theme (e.g., "living room"). You must:
1) Imagine a Setting: Visualize a single room environment fitting that theme.
2) Select Objects:
   - Observer Agent: Character whose LOS determines visibility.
   - Target Agent: Entity on the opposite side.
   - Occluder: Large static object at CENTER of the scene.
3) Set the spatial layout:
   - Occluder at CENTER.
   - Observer on <<OBSERVER_SIDE>>.
   - If starting Visible: Target at diagonal position (opposite-top or opposite-bottom).
   - If starting Occluded: Target directly behind Occluder on opposite side.
4) Design the movement based on <<MOVER>> and <<VISIBILITY_TRANSITION>>.
5) Formulate Ground Truth.
"""

OUTPUT_SCHEMA = """{{
  "scene_meta": {{
    "spatial_scale": "Vista",
    "scene_dynamics": "Dynamic",
    "perspective": "Exo",
    "task_type": "Visibility_Identification",
    "theme": "User's Theme"
  }},
  "objects": [
    {{
      "id": "obj_observer",
      "label": "Theme-appropriate Observer",
      "role": "observer_agent",
      "attributes": {{ "appearance": "...", "position": "Initial position using clock notation. Static: just the clock position (e.g., \\"9 o'clock\\" if OBSERVER_SIDE is Left, \\"3 o'clock\\" if OBSERVER_SIDE is Right). If MOVER == Observer_Moves, format as 'INITIAL_POSITION (initial), moves to FINAL_POSITION' (e.g., \\"9 o'clock (initial), moves to 6 o'clock\\")." }}
    }},
    {{
      "id": "obj_target",
      "label": "Theme-appropriate Target",
      "role": "target_agent",
      "attributes": {{ "appearance": "...", "position": "Initial position relative to Occluder using clock notation (e.g., 12 o'clock above center, 3 o'clock right of center, 6 o'clock below center, 9 o'clock left of center). Static: just the clock position (e.g., \\"12 o'clock\\"). If MOVER == Target_Moves, format as 'INITIAL_POSITION (initial), moves to FINAL_POSITION' (e.g., \\"12 o'clock (initial), moves to 3 o'clock\\")." }}
    }},
    {{
      "id": "obj_occluder",
      "label": "Theme-appropriate Occluder",
      "role": "occluder_object",
      "attributes": {{ "material": "Opaque", "position": "CENTER of the scene" }}
    }}
  ],
  "temporal_flow": {{
    "initial_state": {{
      "description": "Describe layout with diagonal/direct positions and initial LOS status.",
      "observer_view_status": "Visible OR Occluded"
    }},
    "action_sequence": [
      {{
        "step": 1,
        "action_description": "<<MOVER>> moves to change LOS. Describe path and resulting visibility change."
      }}
    ],
    "final_state": {{
      "description": "Describe final layout and LOS status.",
      "observer_view_status": "Visible OR Occluded"
    }}
  }},
  "camera_movement": {{
    "type": "Fixed Angle",
    "trajectory": "Static high-angle exocentric view. Camera does not move. All three entities visible in every frame."
  }},
  "ground_truth": {{
    "visibility_transition": "<<VISIBILITY_TRANSITION>>",
    "mover": "<<MOVER>>",
    "observer_side": "<<OBSERVER_SIDE>>",
    "initial_status": "Visible OR Occluded",
    "final_status": "Occluded OR Visible",
    "trigger_event": "Description of the movement."
  }}
}}"""

EXTRA_PARAMS_CYCLE = [
    {"VISIBILITY_TRANSITION": "Visible_to_Occluded", "OBSERVER_SIDE": "Left", "MOVER": "Target_Moves"},
    {"VISIBILITY_TRANSITION": "Occluded_to_Visible", "OBSERVER_SIDE": "Left", "MOVER": "Target_Moves"},
    {"VISIBILITY_TRANSITION": "Visible_to_Occluded", "OBSERVER_SIDE": "Right", "MOVER": "Target_Moves"},
    {"VISIBILITY_TRANSITION": "Occluded_to_Visible", "OBSERVER_SIDE": "Right", "MOVER": "Target_Moves"},
    {"VISIBILITY_TRANSITION": "Visible_to_Occluded", "OBSERVER_SIDE": "Left", "MOVER": "Observer_Moves"},
    {"VISIBILITY_TRANSITION": "Occluded_to_Visible", "OBSERVER_SIDE": "Left", "MOVER": "Observer_Moves"},
    {"VISIBILITY_TRANSITION": "Visible_to_Occluded", "OBSERVER_SIDE": "Right", "MOVER": "Observer_Moves"},
    {"VISIBILITY_TRANSITION": "Occluded_to_Visible", "OBSERVER_SIDE": "Right", "MOVER": "Observer_Moves"},
]
