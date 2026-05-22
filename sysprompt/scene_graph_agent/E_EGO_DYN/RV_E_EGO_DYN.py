TASK_DEFINITION = """
The ability to identify the relative velocities of multiple moving agents observed from an ego-centric viewpoint. The model must compare each non-ego agent's apparent motion to the ego's reference frame and classify each agent as Slower-than-Ego or Faster-than-Ego based on visual cues.
"""

TASK_RULES = """
1) Reasoning Goal: For each non-ego agent in the scene, classify its velocity relative to the ego as either Slower-than-Ego or Faster-than-Ego. The model must use visual relative-motion cues (apparent backward drift = slower; rapid forward overtake = faster) to make this judgment.
2) Environment: A wide, open path or space appropriate to the theme, allowing agents to travel side by side without lane changes.
3) Ego-Motion: The Ego-agent maintains a constant cruising speed throughout. It does not stop, turn, or change lanes. The Ego is the velocity reference frame.
4) Initial State (visible in first frame):
   - The Ego-agent is moving forward (camera POV).
   - The Slower-than-Ego agent is visible AHEAD of the Ego, in the <<SLOW_SIDE>> lane.
   - The Faster-than-Ego agent is NOT visible at the start — it begins behind the Ego and enters the frame later.
5) Relative Velocities (FIXED): V_FasterAgent > V_Ego > V_SlowerAgent.
6) Velocity Visual Evidence (CRITICAL — these are the signals the model must read):
   - Slower-than-Ego: appears to drift BACKWARD relative to ego in ego's frame (it is barely creeping forward in absolute terms, but ego's higher speed makes it look like it is reversing). It grows larger as ego closes the gap, slides past beside the ego, then drifts off-screen behind.
   - Faster-than-Ego: appears to streak FORWARD relative to ego (it overtakes ego from behind, rapidly shrinks ahead in frame, and disappears into the distance).
"""

TASK_GUIDELINES = """
1. First Frame Specification:
   - Camera: First-person view from inside the Ego-agent, facing straight forward.
   - Visible: Slower agent ahead in the <<SLOW_SIDE>> lane, in its own lane. Path is otherwise clear.
   - Hidden: Faster agent is fully off-screen (behind the Ego — not yet in frame).
   - Establishes the initial baseline: ego cruising forward at constant speed; only the slower agent visible ahead.

2. Camera Movement:
   - Smooth forward motion from ego POV at constant cruising speed.
   - No abrupt stops, turns, lane changes, or speed changes. The camera feels like it is cruising steadily in its own lane.

3. Velocity Visualization (must be unambiguous):
   - Slower agent: appears almost stationary in absolute terms (barely creeping forward). Visually, it grows larger as ego rapidly closes the gap, then slides past beside the ego in the <<SLOW_SIDE>> lane, drifting off-screen behind. From ego's POV, the slower agent visibly moves BACKWARD across the frame.
   - Faster agent: enters from behind in the <<OVERTAKE_SIDE>> lane, streaks past ego at very high relative speed, continues forward, overtakes the slower agent, shrinks to a dot ahead, and disappears.
   - Ego: constant reference frame; no apparent motion of its own (camera-locked, no lane change, no speed change).

4. Spatial Clarity:
   - Slower in the <<SLOW_SIDE>> lane.
   - Faster in the <<OVERTAKE_SIDE>> lane.
   - All three vehicles preserve their own lanes throughout — no lane changes.
"""

FIXED_CONTEXT = """You must strictly adhere to these constraints:
Spatial Scale: Environmental Scale (wide open path or space).
Scene Dynamics: Dynamic Scene (multiple agents moving at different velocities).
Perspective: Ego View (first-person view from the Ego-agent).
Task Logic: Relative Velocity Identification (classify each non-ego agent's velocity as Slower-than-Ego or Faster-than-Ego)."""

CREATIVE_PROCESS = """
The user will provide a Theme (e.g., "Desert Highway", "Ocean Regatta", "Dragon Flightpath"). You must:
1) Define the Ego-Agent: A theme-appropriate moving entity (e.g., car, boat, horse, drone, spacecraft).
2) Create Distinct Agents:
   - Agent A (Slower-than-Ego): Visually distinct (color/type). Starts ahead of Ego in the <<SLOW_SIDE>> lane, moving very slowly (almost stationary).
   - Agent B (Faster-than-Ego): Visually distinct from A. Starts off-screen behind Ego, enters from the <<OVERTAKE_SIDE>> lane, moving much faster than Ego.
3) Choreograph the Velocity Evidence (purely speed-difference, no lane changes):
   - Phase 1: Slower agent in <<SLOW_SIDE>> lane appears nearly frozen; ego rapidly closes the gap; slower agent slides past and drifts off-screen behind (BACKWARD-drift cue).
   - Phase 2: Faster agent enters from behind in <<OVERTAKE_SIDE>> lane; streaks past ego; overtakes the slower agent; shrinks ahead and disappears (FORWARD-streak cue).
4) Formulate Ground Truth: relative velocity classification per agent — obj_slower: Slower-than-Ego; obj_faster: Faster-than-Ego.
"""

OUTPUT_SCHEMA = """{{
  "scene_meta": {{
    "spatial_scale": "Environmental",
    "scene_dynamics": "Dynamic",
    "perspective": "Ego",
    "task_type": "Relative_Velocity_Identification",
    "theme": "User's Theme"
  }},
  "objects": [
    {{
      "id": "obj_ego",
      "label": "Theme-appropriate Ego Agent (e.g., Red Sports Car, White Speedboat)",
      "role": "ego_agent",
      "motion": "Constant cruising speed, forward — velocity reference frame"
    }},
    {{
      "id": "obj_slower",
      "label": "Theme-appropriate Slower Agent (e.g., Yellow Truck, Old Sailboat)",
      "role": "slower_than_ego_agent",
      "visual_attributes": {{ "color": "...", "type": "..." }},
      "position": "Ahead of Ego in the <<SLOW_SIDE>> lane",
      "relative_velocity_to_ego": "Slower-than-Ego (appears to drift backward in ego's frame)"
    }},
    {{
      "id": "obj_faster",
      "label": "Theme-appropriate Faster Agent (e.g., Blue Motorcycle, Racing Jet Ski)",
      "role": "faster_than_ego_agent",
      "visual_attributes": {{ "color": "...", "type": "..." }},
      "position": "Initially off-screen behind Ego in the <<OVERTAKE_SIDE>> lane",
      "relative_velocity_to_ego": "Faster-than-Ego (streaks past ego forward in ego's frame)"
    }}
  ],
  "temporal_flow": {{
    "initial_state": {{
      "description": "Ego cruises forward at constant speed in its own lane. Slower agent visible ahead in the <<SLOW_SIDE>> lane (apparently almost stationary). Faster agent not yet in frame (behind ego)."
    }},
    "action_sequence": [
      {{
        "step": 1,
        "action_description": "Slower agent (in <<SLOW_SIDE>> lane) appears nearly stationary; ego rapidly closes the gap. Slower agent grows larger in frame, slides past ego, drifts off-screen behind — visually appears to move BACKWARD relative to ego (cue: Slower-than-Ego)."
      }},
      {{
        "step": 2,
        "action_description": "Faster agent enters frame from behind in <<OVERTAKE_SIDE>> lane, streaks past ego at very high relative speed (visibly moving FORWARD in ego's frame), continues forward, overtakes the slower agent, shrinks to a dot, disappears ahead into the distance (cue: Faster-than-Ego)."
      }}
    ]
  }},
  "camera_movement": {{
    "type": "Forward Motion Simulation",
    "trajectory": "Straight forward at constant cruising speed from Ego-agent perspective. No lane change."
  }},
  "ground_truth": {{
    "relative_velocity_per_agent": {{
      "obj_slower": "Slower-than-Ego",
      "obj_faster": "Faster-than-Ego"
    }},
    "velocity_ranking_low_to_high": ["obj_slower", "obj_ego", "obj_faster"]
  }}
}}"""

EXTRA_PARAMS_CYCLE = [
    {"SLOW_SIDE": "Right", "OVERTAKE_SIDE": "Left"},
    {"SLOW_SIDE": "Left", "OVERTAKE_SIDE": "Right"},
]
