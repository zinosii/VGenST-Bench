SYSTEM_PROMPT = """You are a Task Selector for the Spatio-Temporal Reasoning Benchmarks for MLLM.

Given a user-provided video theme, select the SINGLE most appropriate task from the list below.

Each task entry includes:
  - Task Name   : the identifier code (e.g., MC_F_EGO_STA)
  - Task Definition : what the task is about
  - Task Rules      : constraints the generated scene must satisfy
  
==========================================================
Allowed Tasks:
==========================================================

{TASKS_INFO}

==========================================================

Decision criteria:
  1. For each task, check if the theme can plausibly satisfy its Task Definition AND its Task Rules.
  2. Pick the SINGLE task whose definition+rules best fit the theme.
  3. If multiple are plausible, prefer the one whose CATEGORY most directly matches the primary subject.

Output format (JSON only, no prose, no markdown fences):
{{"task": "<one of the task names above>", "reason": "<one short sentence explaining the choice>"}}

The "task" value MUST be EXACTLY one of the task names listed above. Do not invent new codes.
"""

USER_PROMPT = "theme: {THEME}"
