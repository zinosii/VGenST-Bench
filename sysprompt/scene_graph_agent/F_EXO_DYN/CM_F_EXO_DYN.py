TASK_DEFINITION = """
The ability to infer the causal mapping between two triggers and two potential effectors, specifically identifying which triggers function correctly and which are 'inert' (broken/dummy) by observing sequential interactions.
"""

TASK_RULES = """
1) Reasoning Goal: Identify which trigger activates which effector by observing the agent interact with each trigger sequentially. Deduce the correct cause-effect mapping.
2) The scene must be a realistic Figural Scale environment (small-scale, graspable objects on a surface).
3) Scene Setup:
   - 2 Distinct Triggers placed in the background (one on the left, one on the right).
   - 2 Distinct Potential Effectors placed in the foreground (one on the left, one on the right).
   - Trigger 1 denotes the FIRST-pressed trigger; Trigger 2 denotes the SECOND-pressed trigger. Each may be on EITHER side.
   - Effector 1 / Effector 2 are just the two effectors present in the scene.
4) One visible agent (human or robot) positioned behind the surface, facing the camera.
5) The camera is fixed in a third-person Exo-view. The agent, both triggers, and both effectors must all be clearly visible throughout the video.
6) Action Sequence (FIXED):
   - Agent presses Trigger 1 -> observe result (Effector 1 reacts, OR nothing happens).
   - Agent retracts hand and pauses briefly.
   - Agent presses Trigger 2 -> observe result (Effector 2 reacts, OR nothing happens).
7) The agent interacts with only ONE trigger at a time. Each reaction must be immediate and synchronous with the press.
8) Scenario type is determined by EXTRA_PARAMS_CYCLE:
   - Scenario A: Both Trigger 1 and Trigger 2 work (Trigger 1 -> Effector 1, Trigger 2 -> Effector 2).
   - Scenario B: Trigger 1 is inert (no reaction). Only Trigger 2 -> Effector 2 works.
   - Scenario C: Trigger 2 is inert (no reaction). Only Trigger 1 -> Effector 1 works.
9) Inert Constraint (CRITICAL): When an inert trigger is pressed, the entire scene must remain ABSOLUTELY STATIC — no effector movement, no lighting change, no camera shake. Only the agent's hand moves (press and release).
"""

TASK_GUIDELINES = """
1. First Frame Specification:
   - Camera: Fixed front-facing Exo view. Slightly elevated angle (~30-45 degrees) so the full surface, both triggers (background), both effectors (foreground), and the agent are all simultaneously visible.
   - Agent: Standing behind the surface, hands at rest (not touching any trigger).
   - All objects (triggers and effectors) in their initial inactive state.

2. Camera Setup:
   - Fixed angle throughout the entire video. No panning, tilting, or zoom.
   - Layout visible: [Agent (far)] -> [Triggers (mid)] -> [Effectors (near camera)].

3. Object Arrangement:
   - One trigger is on the LEFT and the other on the RIGHT (background).
   - One effector is on the LEFT and the other on the RIGHT (foreground).
   - Which side Trigger 1 (first-pressed) occupies is NOT fixed.
   - The effectors' left/right placement is INDEPENDENT of the triggers' placement — an effector may or may not be on the same side as its causally-linked trigger.
   - The causal mapping is revealed only by observing which effector reacts when each trigger is pressed, not by spatial alignment.

4. Effector Reaction Design:
   - Functional Pair: Reaction must be immediate, high-contrast, and unambiguous (e.g., light turns ON, fan starts spinning, flag rises).
   - Inert Pair: Zero reaction. No subtle flicker, no micro-movement. Absolute stillness.
   - The contrast between "reaction" and "no reaction" is the core of the task.

5. Action Pacing:
   - Agent must visibly retract the hand and pause before pressing the next trigger.
   - This separation ensures the model can attribute each effect to the correct trigger.
"""

FIXED_CONTEXT = """You must strictly adhere to these constraints:
Spatial Scale: Figural Space (Small scale, graspable objects).
Scene Dynamics: Dynamic Scene (Actions by an agent).
Perspective: Exo View (Third-person perspective).
Task Logic: Causal Mapping."""

CREATIVE_PROCESS = """
The user will provide only a Theme (e.g., "Magic Show", "Kitchen Preparation"). You must:
1) ONE "Visible Agent" appropriate for the theme.
2) Imagine a Setting: Visualize a flat surface (Anchor) fitting that theme.
3) Select 2 Triggers (Background): Choose buttons/runes/levers.
4) Select 2 Effectors (Foreground): Choose objects that react.
5) SCENARIO TYPE (FIXED): You MUST use Scenario <<SCENARIO_TYPE>>.
  * "A": Both Trigger 1 AND Trigger 2 cause reactions (both work).
  * "B": Trigger 1 is INERT (no reaction). Only Trigger 2 works.
  * "C": Trigger 2 is INERT (no reaction). Only Trigger 1 works.
  DO NOT choose a different scenario. This is fixed for ground truth diversity.
"""

OUTPUT_SCHEMA = """{{
  "scene_meta": {{
    "spatial_scale": "Figural",
    "scene_dynamics": "Dynamic",
    "perspective": "Exo",
    "task_type": "Causal_Mapping",
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
      "id": "obj_anchor",
      "label": "Theme-appropriate Surface (e.g., Wooden Table)",
      "role": "anchor",
      "attributes": {{ "color": "..." }}
    }},
    {{
    "id": "obj_trigger_1",
      "label": "Trigger 1 (first-pressed)",
      "role": "trigger",
      "attributes": {{ "position": "background_left OR background_right (choose freely; Trigger 2 takes the opposite side)" }}
    }},
    {{
      "id": "obj_trigger_2",
      "label": "Trigger 2 (second-pressed)",
      "role": "trigger",
      "attributes": {{ "position": "background_<opposite side of Trigger 1>" }}
    }},
    {{
      "id": "obj_effector_1",
      "label": "Effector 1 (causally linked to Trigger 1)",
      "role": "effector",
      "attributes": {{ "position": "foreground_left OR foreground_right (choose freely; independent of Trigger 1's side)" }}
    }},
    {{
      "id": "obj_effector_2",
      "label": "Effector 2 (causally linked to Trigger 2)",
      "role": "effector",
      "attributes": {{ "position": "foreground_<opposite side of Effector 1>" }}
    }}
  ],
  "temporal_flow": {{
    "initial_setup": {{
      "description": "Both triggers and effectors are placed on the Theme-appropriate Surface, with the Agent positioned to interact."
    }},
    "action_sequence": [
      {{
        "step": 1,
        "action_description": "Agent presses Trigger 1. [Describe Effector 1's reaction, OR 'NOTHING happens — Effector 1 remains completely still.' if Scenario B]"
      }},
      {{
        "step": 2,
        "action_description": "Agent presses Trigger 2. [Describe Effector 2's reaction, OR 'NOTHING happens — Effector 2 remains completely still.' if Scenario C]"
      }}
    ]
  }},
  "camera_movement": {{
    "type": "Fixed Angle",
    "trajectory": "High angle, Static",
  }},
  "ground_truth": {{
    "scenario_type": "<<SCENARIO_TYPE>>",
    "trigger_1_effect": "obj_effector_1 label (if Scenario A or C) OR 'No Effect' (if Scenario B)",
    "trigger_2_effect": "obj_effector_2 label (if Scenario A or B) OR 'No Effect' (if Scenario C)"
  }}
}}"""

EXTRA_PARAMS_CYCLE = [
    {"SCENARIO_TYPE": "A"},
    {"SCENARIO_TYPE": "B"},
    {"SCENARIO_TYPE": "C"},
]
