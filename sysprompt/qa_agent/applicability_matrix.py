QA_TYPES = {
    # L1 Visual Perception
    "L1-OE": {"name": "Object Existence",
              "desc": "Determine whether a specific object or entity appears in any frame in the video."},
    "L1-OA": {"name": "Object Attribute Recognition",
              "desc": "Identify the visual attributes of a specific object in the video, such as color, material."},
    "L1-FL": {"name": "2D Frame Localization",
              "desc": "Identify the 2D position of an object within the frame, in the camera's screen space."},

    # L2 Scene Understanding
    "L2-IT": {"name": "Identity Tracking",
              "desc": "Determine whether two instances observed across different temporal frames, viewpoints, or environmental conditions correspond to the same underlying entity."},
    "L2-AR": {"name": "Action Recognition",
              "desc": "Identify and categorize the specific types of actions or events occurring within the video sequence."},
    "L2-OC": {"name": "Object Counting",
              "desc": "Quantify the exact number of objects that satisfy specific categorical or attribute-based criteria."},
    "L2-TO": {"name": "Temporal Ordering",
              "desc": "Determine the correct chronological sequence of multiple distinct events within the video."},
    "L2-CM": {"name": "Camera Motion Recognition",
              "desc": "Recognizing the camera's motion (e.g., pan, tilt, dolly, boom, zoom)."},
    "L2-SL": {"name": "Spatial Layout Understanding",
              "desc": "Understanding spatial relationships and relative arrangement of objects in the video."},

    # L3 Spatio-Temporal Reasoning
    "L3-PT": {"name": "Perspective-Taking",
              "desc": "Infer the visual representation of a scene from an unobserved, novel viewpoint or perspective not explicitly captured in the video."},
    "L3-CR": {"name": "Counterfactual Reasoning",
              "desc": "Deduce alternative outcomes or states by hypothetically altering specific factual elements or physical conditions within the video."},
    "L3-PR": {"name": "Predictive Reasoning",
              "desc": "Predicting the most probable subsequent events or states following the observed video. This includes predicting how future scenarios will unfold under given specific conditions."},
}


APPLICABILITY_MATRIX = {
    # ---- Figural Scale ----
    "MC_F_EGO_STA": {"L1-OE", "L1-OA", "L1-FL",
                     "L2-IT", "L2-OC", "L2-CM", "L2-SL",
                     "L3-CR"},
    "QC_F_EGO_DYN": {"L1-OE", "L1-OA",
                     "L2-IT", "L2-AR", "L2-OC", "L2-TO", "L2-SL",
                     "L3-CR", "L3-PR"},
    "CI_F_EXO_STA": {"L1-OE", "L1-OA", "L1-FL",
                     "L2-OC", "L2-TO", "L2-CM", "L2-SL",
                     "L3-CR"},
    "CM_F_EXO_DYN": {"L1-OE", "L1-OA", "L1-FL",
                     "L2-AR", "L2-TO", "L2-SL",
                     "L3-PT", "L3-CR"},

    # ---- Vista Scale ----
    "DE_V_EGO_STA": {"L1-OE", "L1-OA",
                     "L2-TO", "L2-CM", "L2-SL",
                     "L3-PT", "L3-CR"},
    "IO_V_EGO_DYN": {"L1-OE", "L1-OA", "L1-FL",
                     "L2-IT", "L2-AR", "L2-OC", "L2-SL",
                     "L3-CR"},
    "HO_V_EXO_STA": {"L1-OE", "L1-OA", "L1-FL",
                     "L2-TO", "L2-CM", "L2-SL",
                     "L3-CR"},
    "VI_V_EXO_DYN": {"L1-OE", "L1-OA", "L1-FL",
                     "L2-IT", "L2-AR", "L2-SL",
                     "L3-PT"},

    # ---- Environmental Scale ----
    "DS_E_EGO_STA": {"L1-OE", "L1-OA", "L1-FL",
                     "L2-OC", "L2-CM", "L2-SL",
                     "L3-PT", "L3-CR"},
    "RV_E_EGO_DYN": {"L1-OE", "L1-OA", "L1-FL",
                     "L2-IT", "L2-AR", "L2-OC", "L2-TO", "L2-CM", "L2-SL",
                     "L3-PT", "L3-CR", "L3-PR"},
    "LS_E_EXO_STA": {"L1-OE", "L1-OA",
                     "L2-TO", "L2-CM", "L2-SL",
                     "L3-PT", "L3-CR", "L3-PR"},
    "BT_E_EXO_DYN": {"L1-OE", "L1-OA",
                     "L2-IT", "L2-AR", "L2-TO", "L2-CM",
                     "L3-PT", "L3-CR"},
}
