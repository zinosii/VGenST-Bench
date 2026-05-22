
import importlib
import json
import logging
import os
from collections import defaultdict

from .base_agent import BaseAgent
from ._examples import load_examples, format_examples
from llm_client import LLMClientFactory

from sysprompt.scenario_agent import scenario_generator as scenario_generator_prompt
from sysprompt.scenario_agent import scenario_validator as scenario_validator_prompt


_EXAMPLES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "sysprompt", "scenario_agent", "examples"
)


# ==========================================
# ScenarioGenerator
# ==========================================
class ScenarioGenerator(BaseAgent):
    def __init__(self, logger, client):
        super().__init__(logger, client)
        self._examples = load_examples(_EXAMPLES_DIR)

    def _example_for(self, task) -> str:
        return format_examples(self._examples.get(task) or [])

    def run(self, task, theme, scene_graph, output_dir, idx, validator_feedback, attempt, save_response=True):
        self.logger.info(
            f"#{idx} [ScenarioGenerator] task: '{task}' theme: '{theme}' "
            f"... (attempt {attempt+1})"
        )

        folder_name = task.split("_", 1)[1]
        module_path = f"sysprompt.scene_graph_agent.{folder_name}.{task}"
        module = importlib.import_module(module_path)

        TASK_DEFINITION = getattr(module, "TASK_DEFINITION")
        TASK_RULES = getattr(module, "TASK_RULES")
        TASK_GUIDELINES = getattr(module, "TASK_GUIDELINES")

        feedback_str = None
        if validator_feedback is not None:
            feedback_str = json.dumps(validator_feedback, indent=2, ensure_ascii=False)

        messages = [
            {"role": "system", "content": scenario_generator_prompt.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": scenario_generator_prompt.USER_PROMPT.format(
                    SCENE_GRAPH=scene_graph,
                    TASK_DEFINITION=TASK_DEFINITION,
                    TASK_RULES=TASK_RULES,
                    TASK_GUIDELINES=TASK_GUIDELINES,
                    EXAMPLE=self._example_for(task),
                    FEEDBACK=feedback_str,
                ),
            },
        ]

        response = self.query_llm(messages)
        scenario = self.fix_json(response)

        full_path = ""
        if save_response and scenario is not None:
            out = os.path.join(output_dir, "scenario_agent", task, "scenario_generator")
            os.makedirs(out, exist_ok=True)
            safe_theme = theme.replace(" ", "_")
            full_path = os.path.join(out, f"{idx}_{safe_theme}_{attempt}.json")
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(scenario, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Saved: '{full_path}'")
        return scenario, full_path


# ==========================================
# ScenarioValidator
# ==========================================
class ScenarioValidator(BaseAgent):
    def run(self, task, theme, scene_graph, scenario, output_dir, idx, attempt, save_response=True):
        self.logger.info(
            f"#{idx} [ScenarioValidator] task: '{task}' theme: '{theme}' "
            f"... (attempt {attempt+1})"
        )

        folder_name = task.split("_", 1)[1]
        module_path = f"sysprompt.scene_graph_agent.{folder_name}.{task}"
        module = importlib.import_module(module_path)

        TASK_DEFINITION = getattr(module, "TASK_DEFINITION")
        TASK_RULES = getattr(module, "TASK_RULES")
        TASK_GUIDELINES = getattr(module, "TASK_GUIDELINES")

        messages = [
            {"role": "system", "content": scenario_validator_prompt.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": scenario_validator_prompt.USER_PROMPT.format(
                    SCENE_GRAPH=scene_graph,
                    TASK_DEFINITION=TASK_DEFINITION,
                    TASK_RULES=TASK_RULES,
                    TASK_GUIDELINES=TASK_GUIDELINES,
                    SCENARIO=scenario,
                ),
            },
        ]

        response = self.query_llm(messages)
        feedback = self.fix_json(response)

        full_path = ""
        if save_response and feedback is not None:
            out = os.path.join(output_dir, "scenario_agent", task, "scenario_validator")
            os.makedirs(out, exist_ok=True)
            safe_theme = theme.replace(" ", "_")
            full_path = os.path.join(out, f"{idx}_{safe_theme}_validation_{attempt}.json")
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(feedback, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Saved: '{full_path}'")

        return feedback, full_path


# ==========================================
# ScenarioAgent
# ==========================================
class ScenarioAgent:
    def __init__(
        self,
        logger: logging.Logger,
        client_factory: LLMClientFactory,
        config: dict,
    ):
        self.logger = logger
        self.config = config
        self.scenario_output = defaultdict(list)

        self.generator_cfg = config["scenario_generator"]
        self.validator_cfg = config["scenario_validator"]

        self.generator = ScenarioGenerator(
            logger=logger,
            client=client_factory.build(self.generator_cfg),
        )
        self.validator = ScenarioValidator(
            logger=logger,
            client=client_factory.build(self.validator_cfg),
        )

    def run(self, task, theme, scene_graph, output_dir, idx, save_response=True):
        max_retries = self.validator_cfg["max_retries"]
        validator_feedback = None
        last_scenario, last_path = None, None

        for attempt in range(max_retries):
            scenario, scenario_path = self.generator.run(
                task, theme, scene_graph, output_dir, idx,
                validator_feedback, attempt, save_response,
            )
            last_scenario, last_path = scenario, scenario_path

            if scenario is None:
                self.logger.warning(
                    f"Generator returned None on attempt {attempt+1}. Skipping validation."
                )
                continue

            validation_result, _ = self.validator.run(
                task, theme, scene_graph, scenario, output_dir, idx, attempt, save_response,
            )

            if validation_result is None:
                self.logger.warning(
                    f"Validator returned None on attempt {attempt+1}. Treating as failed."
                )
                continue

            if validation_result.get("is_valid"):
                self.logger.info(f"Scenario validated on attempt {attempt+1}.")
                self.scenario_output[task].append([theme, scenario, scenario_path])
                return scenario, scenario_path

            self.logger.warning(
                f"Validation failed for '{scenario_path}'. "
                f"Retrying ({attempt+1}/{max_retries})."
            )
            validator_feedback = validation_result

        self.logger.warning(
            f"Max retries ({max_retries}) exceeded. Using last scenario."
        )
        if last_scenario is not None:
            self.scenario_output[task].append([theme, last_scenario, last_path])
        return last_scenario, last_path
