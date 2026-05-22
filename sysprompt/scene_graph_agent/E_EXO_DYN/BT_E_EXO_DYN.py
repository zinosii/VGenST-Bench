TASK_DEFINITION = """
The ability to identify the specific environmental stimulus that caused a sudden change in an agent's locomotion behavior. The model must distinguish the dynamic causal trigger from a static side distractor, and causally link the observed reaction to the correct trigger.
"""

TASK_RULES = """
1) Reasoning Goal: "Why did the agent react?" — Link the maneuver to the dynamic trigger object (NOT the static side distractor).
2) Environment: Realistic Environmental Scale (Long Road, Park Path, Warehouse Aisle). The path must be long enough to establish a clear baseline trajectory before the trigger appears.
3) Agent: A single moving entity (Car, Cyclist, Robot, Human) initially following a predictable straight path at constant speed.
4) The Side Distractor (visual scene element):
   - A theme-appropriate static object placed on one side of the path (left or right), positioned adjacent to the path.
   - Examples: parked delivery van, bus stop shelter, mailbox cluster, dumpster, hedge, stacked crates, vendor kiosk, market stall, parked truck, utility box, tree, dock, pylon.
5) The Trigger (Sudden On-Path Appearance — CRITICAL):
   - The trigger SUDDENLY ENTERS the camera frame and appears on the agent's path. 
   - Trigger types: A dynamic hazard that intrudes onto the path (e.g., a rolling ball, an animal running across, a person stepping in, a vehicle swerving into the lane, a falling object).
6) The Reaction Type is <<REACTION_TYPE>>:
   - "Full_Stop": Agent decelerates rapidly and comes to a complete standstill. Does NOT resume.
   - "Wait_and_Resume": Agent slows to a stop and waits while the dynamic trigger passes through. Once the path is clear, agent resumes forward motion in the original direction.
"""

TASK_GUIDELINES = """
1. First Frame Specification:
   - Camera: High-angle drone view, tracking the agent from slightly behind and above.
   - Visible: Agent is moving forward along a clear, unobstructed straight path. The Side Distractor is visible adjacent to the path on the side designated by <<DISTRACTOR_POSITION>>.

2. Side Distractor Design:
   - Placement: Adjacent to the path on the <<DISTRACTOR_POSITION>> side. 
   - Size: Any reasonable size for the theme. No requirement to be large enough to hide anything.
   - Theme-appropriate: Natural fit for the environment (e.g., downtown = parked van/bus stop/vendor cart; park = hedge/gazebo/bench cluster; warehouse = stacked crates/forklift; rural road = hay bale stack/tree; water = dock/pylon/buoy).
   
3. Camera Movement (High-Angle Drone Tracking):
   - The camera moves WITH the agent, keeping the agent in the lower-center of the frame.
   - The camera should travel through the environment (not just pan from a fixed point) to show the full extent of the path.
   - No cuts, jump cuts, or teleportation.

4. Temporal Pacing (The "Sudden Appearance" Mechanics):
   - Phase 1 (Baseline): Agent moves forward at constant speed on a completely clear path. Side Distractor is visible on the <<DISTRACTOR_POSITION>> side.
   - Phase 2 (Trigger Enters Frame): The trigger object SUDDENLY ENTERS the camera frame from outside the visible area and appears directly on the agent's path. 
   - Phase 3 (Reaction): Agent immediately performs the <<REACTION_TYPE>> maneuver. The reaction must be visually distinct and unambiguous.

5. Reaction Clarity:
   - Full_Stop: Agent comes to a COMPLETE stop — not just slowing down. Remains stationary. Video ends with agent stopped.
   - Wait_and_Resume: Agent decelerates to a complete stop and holds position while the trigger (a moving hazard) passes through the path. Once the path is clear, agent visibly accelerates and resumes.
"""

FIXED_CONTEXT = """Spatial Scale: Environmental Scale (long road, park path, warehouse aisle).
Scene Dynamics: Dynamic Scene (agent moves; trigger object intrudes dynamically).
Perspective: Exo View (high-angle drone tracking the agent).
Task Logic: Behavioral Trigger Identification."""

CREATIVE_PROCESS = """
The user will provide a Theme (e.g., "Airport Terminal", "Park Jogging Trail"). You must:
1) Define the Agent: A moving entity appropriate to the theme (e.g., Yellow Taxi, Jogger, Delivery Robot).
2) Define the Side Distractor: A theme-appropriate static object placed on the <<DISTRACTOR_POSITION>> side of the path.
3) Define the Trigger: A dynamic hazard natural to the theme (e.g., Rolling luggage cart, Dog running across, ball bouncing into path, vehicle swerving in, person stepping out, falling object).
4) Reaction Type (FIXED): The agent MUST perform <<REACTION_TYPE>>. Do NOT use a different reaction.
"""

OUTPUT_SCHEMA = """{{
  "scene_meta": {{
    "spatial_scale": "Environmental",
    "scene_dynamics": "Dynamic",
    "perspective": "Exo",
    "task_type": "Behavioral_Trigger_Identification",
    "theme": "User's Theme"
  }},
  "objects": [
    {{
      "id": "obj_agent",
      "label": "Theme-appropriate Moving Agent (e.g., Jogger in Blue)",
      "role": "agent",
      "attributes": {{ "color": "...", "type": "..." }}
    }},
    {{
      "id": "obj_distractor",
      "label": "Theme-appropriate Static Side Distractor (e.g., Parked Delivery Van, Tall Hedge, Dumpster)",
      "role": "distractor",
      "attributes": {{ "color": "...", "type": "...", "position": "<<DISTRACTOR_POSITION>> side of path" }}
    }},
    {{
      "id": "obj_trigger",
      "label": "Theme-appropriate Trigger Object (e.g., Running Dog, Rolling Ball, Vehicle)",
      "role": "trigger",
      "attributes": {{ "entry_direction": "<<DISTRACTOR_POSITION>> side of path" }}
    }}
  ],
  "temporal_flow": {{
    "initial_state": {{
      "description": "Agent is moving forward along a clear, unobstructed path. The Side Distractor is visible on the <<DISTRACTOR_POSITION>> side of the path as a static scene element."
    }},
    "action_sequence": [
      {{
        "step": 1,
        "action_description": "Agent moves at constant speed on a clear path. Path ahead is unobstructed. Side Distractor is visible on the <<DISTRACTOR_POSITION>> side of the path."
      }},
      {{
        "step": 2,
        "action_description": "[Trigger object] enters the camera frame from the <<DISTRACTOR_POSITION>> side and appears on the agent's path."
      }},
      {{
        "step": 3,
        "action_description": "Agent immediately performs <<REACTION_TYPE>> maneuver in response to the trigger."
      }}
    ]
  }},
  "camera_movement": {{
    "type": "High-Angle Drone Tracking",
    "trajectory": "Camera follows agent from behind at high angle, traveling forward with the agent throughout the scene."
  }},
  "ground_truth": {{
    "trigger_object_id": "obj_trigger",
    "trigger_object_label": "Trigger object label here",
    "reaction_type": "<<REACTION_TYPE>>"
  }}
}}"""

EXTRA_PARAMS_CYCLE = [
    {"REACTION_TYPE": "Full_Stop", "DISTRACTOR_POSITION": "left"},
    {"REACTION_TYPE": "Full_Stop", "DISTRACTOR_POSITION": "right"},
    {"REACTION_TYPE": "Wait_and_Resume", "DISTRACTOR_POSITION": "left"},
    {"REACTION_TYPE": "Wait_and_Resume", "DISTRACTOR_POSITION": "right"},
]
