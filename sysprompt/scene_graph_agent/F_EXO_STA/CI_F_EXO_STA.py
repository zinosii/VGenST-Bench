TASK_DEFINITION = """
The ability to identify the objects shared by both of two opaque open-top containers, by integrating two sequential overhead-peek observations — each fully revealing all three contents of one container — and finding the intersections of the two revealed sets.
"""

TASK_RULES = """
1) Reasoning Goal: Identify ALL objects that appear in BOTH Container A AND Container B. The answer is the intersection of the two sets. Neither phase alone provides the answer — both must be integrated.
2) The scene must be a realistic Figural Scale environment (small-scale objects inside containers on a surface).
3) All objects remain absolutely stationary throughout the entire video. Only the camera is allowed to move.
4) Exactly two opaque OPEN-TOP containers on the surface, each holding EXACTLY THREE objects:
   - Container A: three small objects (freely chosen).
   - Container B: three small objects (freely chosen).
   - Exactly <<NUM_SHARED>> object(s) must appear in BOTH containers (IDENTICAL OBJECTS). These are the correct answer(s).
   - The remaining objects in each container are unique to that container.
5) Phase 1 — Container A Reveal: Camera moves left, overhead to look inside Container A. All three objects are clearly visible. Container B's interior is completely off-screen.
6) Phase 2 — Container B Reveal: Camera moves right to look inside Container B. All three objects are clearly visible. Container A's interior is no longer visible.
7) The correct answer is the set of ALL objects that appeared in BOTH containers — exactly <<NUM_SHARED>> object(s).
"""

TASK_GUIDELINES = """
1. Container Design:
   - Both containers MUST be OPEN-TOP with NO lid — the camera must be able to see directly inside from above.
   - Both containers must be OPAQUE with no see-through sections (ceramic crate, wooden box, metal bucket, wicker basket, cardboard box).
   - Containers must be visually distinct from each other (different material, color, and shape).
   - Each container must be large and wide enough that all THREE objects inside are clearly visible and individually distinguishable from the overhead camera.

2. Object Design:
   - Objects must be small.
   - SHARED OBJECTS: exactly <<NUM_SHARED>> object(s) must appear identically (same type, same color) in BOTH containers. Each shared object must be immediately recognizable as the same object when seen in Phase 2.
   - UNIQUE OBJECTS: the remaining (3 - <<NUM_SHARED>>) objects in each container must be unique to that container and clearly distinct from one another.
   - All objects must be theme-appropriate, small-scale, and individually distinguishable from the overhead view.

3. Camera Movement Sequence:
   Phase 1 — Container A Reveal:
     - Camera starts at table-height, showing both open-top containers from the side. Neither interior is visible.
     - Camera smoothly moves to an overhead position above Container A.
     - ALL THREE objects inside Container A are fully visible from above, clearly separated and individually identifiable.
     - Container B's interior remains hidden (wrong angle, or off-screen entirely).

   Phase 2 — Container B Reveal:
     - Camera smoothly moves from Container A to an overhead position above Container B.
     - Container A's interior is now completely invisible.
     - ALL THREE objects inside Container B are fully visible from above, clearly separated.

4. Critical Constraints:
   - Both containers MUST be open-top — no lids, flaps, or covers of any kind.
   - Container A's interior MUST BE INVISIBLE during Phase 2 — camera has fully moved away.
   - Container B's interior MUST BE INVISIBLE during Phase 1.
   - Each shared object MUST LOOK IDENTICAL (same type, same color) in both containers.
   - All objects remain completely stationary. No movement of any object at any point.
"""

FIXED_CONTEXT = """You must strictly adhere to these constraints:
Spatial Scale: Figural Space (Small scale, graspable objects inside containers).
Scene Dynamics: Static Scene (Objects do not move; only the camera moves).
Perspective: Exo View (Third-person overhead camera).
Task Logic: Container Intersection Inference."""

CREATIVE_PROCESS = """
The user will provide only a Theme (e.g., "Kitchen Counter", "Toy Chest", "Office Desk"). You must:
1) Design Two Containers: Choose two visually distinct opaque OPEN-TOP containers (no lids) that fit the theme. Container A is revealed first (Phase 1), Container B is revealed second (Phase 2).
2) Choose exactly <<NUM_SHARED>> SHARED OBJECT(S): small, recognizable, theme-appropriate object(s) that appear IDENTICALLY (same type, same color) in BOTH containers.
3) Fill Container A's remaining (3 - <<NUM_SHARED>>) slots with unique, theme-appropriate objects distinct from the shared object(s) and from each other.
4) Fill Container B's remaining (3 - <<NUM_SHARED>>) slots with different unique objects, also distinct from the shared object(s) and from each other.
5) Plan Camera Path:
   - Start: Table-height side view showing both open-top containers from the side (no interior visible).
   - Phase 1: Camera moves overhead Container A → reveals all 3 objects. Container B interior hidden.
   - Phase 2: Camera moves overhead Container B → reveals all 3 objects. Container A interior hidden.
6) Verify Ground Truth: Confirm that exactly <<NUM_SHARED>> object type(s) appear in BOTH Container A and Container B.
"""

OUTPUT_SCHEMA = """{{
  "scene_meta": {{
    "spatial_scale": "Figural",
    "scene_dynamics": "Static",
    "perspective": "Exo",
    "task_type": "Container_Intersection_Inference",
    "theme": "User's Theme"
  }},
  "objects": [
    {{
      "id": "obj_surface",
      "label": "Theme-appropriate surface (e.g., Wooden Kitchen Counter)",
      "role": "anchor"
    }},
    {{
      "id": "container_A",
      "label": "Theme-appropriate opaque OPEN-TOP container",
      "role": "Container A",
      "attributes": {{
        "revealed_in": "Phase 1",
        "color": "..."
      }},
    }},
    {{
      "id": "obj_A1", 
      "label": "...", 
      "role": "container_A_object_1", 
      "attributes": {{
        "color": "...", 
        "type": "..."
      }}
    }},
    {{
      "id": "obj_A2", 
      "label": "...", 
      "role": "container_A_object_2", 
      "attributes": {{
        "color": "...", 
        "type": "..."
      }}
    }},
    {{
      "id": "obj_A3", 
      "label": "...", 
      "role": "container_A_object_3", 
      "attributes": {{
        "color": "...", 
        "type": "..."
      }}
    }},
    {{
      "id": "container_B",
      "label": "Theme-appropriate opaque OPEN-TOP container",
      "role": "Container B",
      "attributes": {{
        "revealed_in": "Phase 2",
        "color": "..."
      }},
    }},
    {{
      "id": "obj_B1", 
      "label": "...", 
      "role": "container_B_object_1", 
      "attributes": {{
        "color": "...", 
        "type": "..."
      }}
    }},
    {{
      "id": "obj_B2", 
      "label": "...", 
      "role": "container_B_object_2", 
      "attributes": {{
        "color": "...", 
        "type": "..."
      }}
    }},
    {{
      "id": "obj_B3", 
      "label": "...", 
      "role": "container_B_object_3", 
      "attributes": {{
        "color": "...", 
        "type": "..."
      }}
    }}
  ],
  "temporal_flow": {{
    "initial_setup": {{
      "description": "Table-height side view. Both open-top containers visible from the side. No interior visible."
    }},
    "action_sequence": [
      {{
        "step": 1,
        "action_description": "Camera moves overhead Container A. All three objects clearly visible from above, individually distinguishable. Container B interior completely hidden.",  
      }},
      {{
        "step": 2,
        "action_description": "Camera moves overhead Container B. All three objects clearly visible from above, individually distinguishable. Container A interior completely hidden."
      }}
    ]
  }},
  "camera_movement": {{
    "type": "Sequential Overhead Peek — Two Containers",
    "trajectory": "Table-height side view. Both open-top containers visible from the side. No interior visible. → Camera moves overhead Container A (Ceramic Crate). All three objects — Small Red Pillar Candle, Small Wooden Picture Frame, Small Silver Fork — clearly visible from above. Container B interior completely hidden. Camera holds 2+ seconds. → Camera moves overhead Container B (Wicker Basket). All three objects — Small Green Glass Tealight Holder, Small Silver TV Remote Control, Small Brown Leather Keychain — clearly visible from above. Container A interior completely hidden."
  }},
  "ground_truth": {{
    "container_A_contents": ["obj_A1 label", "obj_A2 label", "obj_A3 label"],
    "container_B_contents": ["obj_B1 label", "obj_B2 label", "obj_B3 label"],
    "num_shared": <<NUM_SHARED>>,
    "shared_objects": ["label of each object appearing in both containers — empty list if none"],
    "answer": "List the shared object label(s), or 'None' if num_shared is 0",
    "reasoning": "<<REASONING>>"
  }}
}}"""

EXTRA_PARAMS_CYCLE = [
    {
        "NUM_SHARED": "0",
        "REASONING": "Phase 1 reveals Container A: 3 objects. Phase 2 reveals Container B: 3 completely different objects with no overlap. Intersection: empty. Answer: None.",
    },
    {
        "NUM_SHARED": "1",
        "REASONING": "Phase 1 reveals Container A: 3 objects including 1 shared object. Phase 2 reveals Container B: 3 objects including the same shared object (identical). Intersection: 1 object. Answer: [the shared object].",
    },
    {
        "NUM_SHARED": "2",
        "REASONING": "Phase 1 reveals Container A: 3 objects including 2 shared objects. Phase 2 reveals Container B: 3 objects including the same 2 shared objects (identical). Intersection: 2 objects. Answer: [the two shared objects].",
    },
    {
        "NUM_SHARED": "3",
        "REASONING": "Phase 1 reveals Container A: 3 objects, all of which also appear in Container B. Phase 2 reveals Container B: the exact same 3 objects. Intersection: all 3 objects. Answer: [all three objects].",
    },
]
