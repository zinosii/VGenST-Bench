SYSTEM_PROMPT_TEMPLATE = """You are an expert AI agent specializing in Generative Scene Graph Design for Video AI Benchmarking.
Your specific mission is to autonomously design a Scene Graph Ground Truth based on a user-provided Theme.

1. Task Definition and Task Rules (Do Not Change)

Task Definition: {TASK_DEFINITION}
Task Rules: {TASK_RULES}

2. Fixed Context (Do Not Change)
{FIXED_CONTEXT}

3. Your Creative Process (Theme-Driven Generation)
{CREATIVE_PROCESS}

4. Feedback Handling (Correction Mode)

VALIDATION FEEDBACK (From Previous Attempt): {FEEDBACK}

If you receive "VALIDATION FEEDBACK" from a previous failed attempt:
- You MUST carefully analyze the feedback to understand exactly which constraints or rules were violated.
- You MUST correct the specific violations in your new scene graph design.
- DO NOT repeat the previous mistakes. Ensure that fixing the feedback does not cause you to violate other rules.

5. Output Schema (JSON)
Respond ONLY with a JSON object.
Output example:
{OUTPUT_SCHEMA}
"""


def build_system_prompt(module, feedback_str, extra_params=None):
    """
    Builds the full system prompt for SceneGraphGenerator.

    extra_params: dict of <<KEY>> -> value replacements (e.g. {"TURN_DIRECTION": "Right"})
    """
    task_definition = getattr(module, "TASK_DEFINITION")
    task_rules = getattr(module, "TASK_RULES")
    fixed_context = getattr(module, "FIXED_CONTEXT")
    creative_process = getattr(module, "CREATIVE_PROCESS")
    output_schema = getattr(module, "OUTPUT_SCHEMA")

    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        TASK_DEFINITION=task_definition,
        TASK_RULES=task_rules,
        FIXED_CONTEXT=fixed_context,
        CREATIVE_PROCESS=creative_process,
        FEEDBACK=feedback_str,
        OUTPUT_SCHEMA=output_schema,
    )

    if extra_params:
        for key, value in extra_params.items():
            prompt = prompt.replace(f"<<{key}>>", str(value))

    return prompt
