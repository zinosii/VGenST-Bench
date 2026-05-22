import importlib
import json
import logging
import os
from collections import defaultdict

from utils.settings import TARGET_TASKS

from .base_agent import BaseAgent
from llm_client import LLMClientFactory

from sysprompt.scene_graph_agent import scene_graph_validator as scene_graph_validator_prompt
from sysprompt.scene_graph_agent import generator_template
from sysprompt.scene_graph_agent import task_selector as task_selector_prompt


TARGET_TASKS_SET = set(TARGET_TASKS)


# ==========================================
# TaskSelector
# ==========================================
class TaskSelector(BaseAgent):
    def __init__(self, logger, client):
        super().__init__(logger, client)
        self._tasks_info = self._build_tasks_info()

    @staticmethod
    def _build_tasks_info() -> str:
        blocks = []
        for task in TARGET_TASKS:
            folder_name = task.split("_", 1)[1]
            module_path = f"sysprompt.scene_graph_agent.{folder_name}.{task}"
            module = importlib.import_module(module_path)

            definition = getattr(module, "TASK_DEFINITION", "").strip()
            rules = getattr(module, "TASK_RULES", "").strip()
            blocks.append(
                f"### {task}\n"
                f"Task Definition:\n{definition}\n\n"
                f"Task Rules:\n{rules}"
            )
        return "\n\n----------------------------------------\n\n".join(blocks)

    def run(self, theme):
        self.logger.info(f"[TaskSelector] theme: '{theme}' ...")

        messages = [
            {
                "role": "system",
                "content": task_selector_prompt.SYSTEM_PROMPT.format(
                    TASKS_INFO=self._tasks_info
                ),
            },
            {
                "role": "user",
                "content": task_selector_prompt.USER_PROMPT.format(THEME=theme),
            },
        ]

        response = self.query_llm(messages)
        parsed = self.fix_json(response)
        if not isinstance(parsed, dict):
            self.logger.error(f"[TaskSelector] invalid response: {response!r}")
            return None

        task = parsed.get("task")
        reason = parsed.get("reason", "")
        self.logger.info(f"[TaskSelector] -> {task!r} ({reason})")
        return task


# ==========================================
# SceneGraphGenerator
# ==========================================
class SceneGraphGenerator(BaseAgent):
    def run(self, task, theme, output_dir, idx, validator_feedback, attempt, save_response=True):
        self.logger.info(
            f"#{idx} [SceneGraphGenerator] task: '{task}' theme: '{theme}' "
            f"... (attempt {attempt+1})"
        )

        folder_name = task.split("_", 1)[1]
        module_path = f"sysprompt.scene_graph_agent.{folder_name}.{task}"
        module = importlib.import_module(module_path)

        feedback_str = None
        if validator_feedback is not None:
            feedback_str = json.dumps(validator_feedback, indent=2, ensure_ascii=False)

        extra_params_cycle = getattr(module, "EXTRA_PARAMS_CYCLE", None)
        extra_params = (
            extra_params_cycle[idx % len(extra_params_cycle)] if extra_params_cycle else None
        )
        system_prompt = generator_template.build_system_prompt(
            module, feedback_str, extra_params
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"theme = {theme}"},
        ]

        response = self.query_llm(messages)
        scene_graph = self.fix_json(response)

        full_path = ""
        if save_response and scene_graph is not None:
            out = os.path.join(output_dir, "scene_graph_agent", task, "scene_graph_generator")
            os.makedirs(out, exist_ok=True)
            safe_theme = theme.replace(" ", "_")
            full_path = os.path.join(out, f"{idx}_{safe_theme}_{attempt}.json")
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(scene_graph, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Saved: '{full_path}'")

        return scene_graph, full_path


# ==========================================
# SceneGraphValidator
# ==========================================
class SceneGraphValidator(BaseAgent):
    def run(self, task, theme, scene_graph, output_dir, idx, attempt, save_response=True):
        self.logger.info(
            f"#{idx} [SceneGraphValidator] task: '{task}' theme: '{theme}' "
            f"... (attempt {attempt+1})"
        )

        folder_name = task.split("_", 1)[1]
        module_path = f"sysprompt.scene_graph_agent.{folder_name}.{task}"
        module = importlib.import_module(module_path)

        TASK_DEFINITION = getattr(module, "TASK_DEFINITION")
        TASK_RULES = getattr(module, "TASK_RULES")

        messages = [
            {"role": "system", "content": scene_graph_validator_prompt.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": scene_graph_validator_prompt.USER_PROMPT.format(
                    TASK_DEFINITION=TASK_DEFINITION,
                    TASK_RULES=TASK_RULES,
                    THEME=theme,
                    SCENE_GRAPH=scene_graph,
                ),
            },
        ]

        response = self.query_llm(messages)
        feedback = self.fix_json(response)

        full_path = ""
        if save_response and feedback is not None:
            out = os.path.join(output_dir, "scene_graph_agent", task, "scene_graph_validator")
            os.makedirs(out, exist_ok=True)
            safe_theme = theme.replace(" ", "_")
            full_path = os.path.join(out, f"{idx}_{safe_theme}_validation_{attempt}.json")
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(feedback, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Saved: '{full_path}'")

        return feedback, full_path


# ==========================================
# SceneGraphAgent
# ==========================================
class SceneGraphAgent:
    def __init__(
        self,
        logger: logging.Logger,
        client_factory: LLMClientFactory,
        config: dict,
    ):
        self.logger = logger
        self.config = config
        self.scene_graph_output = defaultdict(list)

        self.task_selector_cfg = config["task_selector"]
        self.generator_cfg = config["scene_graph_generator"]
        self.validator_cfg = config["scene_graph_validator"]

        self.task_selector = TaskSelector(
            logger=logger,
            client=client_factory.build(self.task_selector_cfg),
        )
        self.generator = SceneGraphGenerator(
            logger=logger,
            client=client_factory.build(self.generator_cfg),
        )
        self.validator = SceneGraphValidator(
            logger=logger,
            client=client_factory.build(self.validator_cfg),
        )

    def _select_task(self, theme):
        task = self.task_selector.run(theme)
        if task not in TARGET_TASKS_SET:
            self.logger.error(
                f"[task_selector] invalid task {task!r} for theme {theme!r} "
                f"(not in TARGET_TASKS). Skipping."
            )
            return None
        return task

    def run(self, theme, output_dir, idx, task=None, save_response=True):
        if task is None:
            task = self._select_task(theme)
            if task is None:
                return None, None

        max_retries = self.validator_cfg["max_retries"]
        validator_feedback = None
        last_scene_graph, last_path = None, None

        for attempt in range(max_retries):
            scene_graph, scene_graph_path = self.generator.run(
                task, theme, output_dir, idx, validator_feedback, attempt, save_response
            )
            last_scene_graph, last_path = scene_graph, scene_graph_path

            if scene_graph is None:
                self.logger.warning(
                    f"Generator returned None on attempt {attempt+1}. Skipping validation."
                )
                continue

            validation_result, _ = self.validator.run(
                task, theme, scene_graph, output_dir, idx, attempt, save_response
            )

            if validation_result is None:
                self.logger.warning(
                    f"Validator returned None on attempt {attempt+1}. Treating as failed."
                )
                continue

            if validation_result.get("is_valid"):
                self.logger.info(f"Scene Graph validated on attempt {attempt+1}.")
                self.scene_graph_output[task].append(
                    [theme, scene_graph, scene_graph_path]
                )
                return scene_graph, scene_graph_path

            self.logger.warning(
                f"Validation failed for '{scene_graph_path}'. "
                f"Retrying ({attempt+1}/{max_retries})."
            )
            validator_feedback = validation_result

        self.logger.warning(
            f"Max retries ({max_retries}) exceeded. Using last scene graph."
        )
        if last_scene_graph is not None:
            self.scene_graph_output[task].append([theme, last_scene_graph, last_path])
        return last_scene_graph, last_path
