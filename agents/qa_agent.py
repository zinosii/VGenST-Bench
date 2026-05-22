
import importlib
import json
import logging
import os
from collections import defaultdict

from .base_agent import BaseAgent
from llm_client import LLMClientFactory

from sysprompt.qa_agent import qa_generator as qa_generator_prompt
from sysprompt.qa_agent import reformatter as reformatter_prompt
from sysprompt.qa_agent.applicability_matrix import APPLICABILITY_MATRIX, QA_TYPES


_PROTOTYPES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "sysprompt", "qa_agent", "tasks"
)


# ==========================================
# QAGenerator 
# ==========================================
class QAGenerator(BaseAgent):
    def run(self, task, qa_type, theme, scene_graph, scenario, output_dir, idx,
            distractor_pool=None, save_response=True):
        self.logger.info(
            f"#{idx} [QAGenerator] task: '{task}' qa_type: '{qa_type}' theme: '{theme}' ..."
        )


        proto_path = os.path.join(_PROTOTYPES_DIR, task, f"{qa_type}.json")
        if not os.path.exists(proto_path):
            self.logger.warning(
                f"[QAGenerator] prototype not found: {proto_path} — skipping (task={task}, qa_type={qa_type})"
            )
            return None, ""

        try:
            with open(proto_path, "r", encoding="utf-8") as f:
                proto_data = json.load(f)
        except Exception as e:
            self.logger.error(f"[QAGenerator] failed to load prototype {proto_path}: {e}")
            return None, ""

        prototypes_str = json.dumps(proto_data, indent=2, ensure_ascii=False)


        folder_name = task.split("_", 1)[1]
        module_path = f"sysprompt.scene_graph_agent.{folder_name}.{task}"
        module = importlib.import_module(module_path)
        TASK_DEFINITION = getattr(module, "TASK_DEFINITION")
        TASK_RULES = getattr(module, "TASK_RULES")


        qa_type_info = QA_TYPES.get(qa_type, {})
        qa_type_name = qa_type_info.get("name", qa_type)
        qa_type_def = qa_type_info.get("desc", "(no definition)")

        if distractor_pool:
            distractor_pool_str = json.dumps(distractor_pool, indent=2, ensure_ascii=False)
        else:
            distractor_pool_str = "(none available)"

        messages = [
            {"role": "system", "content": qa_generator_prompt.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": qa_generator_prompt.USER_PROMPT.format(
                    TASK_ID=task,
                    TASK_DEFINITION=TASK_DEFINITION,
                    TASK_RULES=TASK_RULES,
                    QA_TYPE_ID=qa_type,
                    QA_TYPE_NAME=qa_type_name,
                    QA_TYPE_DEF=qa_type_def,
                    SCENE_GRAPH=scene_graph,
                    SCENARIO=scenario,
                    PROTOTYPES=prototypes_str,
                    DISTRACTOR_POOL=distractor_pool_str,
                ),
            },
        ]

        response = self.query_llm(messages)
        qa_result = self.fix_json(response)

        full_path = ""
        if save_response and qa_result is not None:
            out = os.path.join(output_dir, "qa_agent", task, qa_type, "qa_generator")
            os.makedirs(out, exist_ok=True)
            safe_theme = theme.replace(" ", "_")
            full_path = os.path.join(out, f"{idx}_{safe_theme}.json")
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(qa_result, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Saved: '{full_path}'")

        return qa_result, full_path


# ==========================================
# Reformatter
# ==========================================
class Reformatter(BaseAgent):
    def run(self, task, qa_type, base_qa, theme, output_dir, idx, save_response=True):
        if not base_qa or not base_qa.get("questions"):
            self.logger.warning(
                f"[Reformatter] no base questions to reformat (task={task}, qa_type={qa_type})"
            )
            return None, ""

        self.logger.info(
            f"#{idx} [Reformatter] task: '{task}' qa_type: '{qa_type}' theme: '{theme}' "
            f"({len(base_qa['questions'])} base Qs)"
        )

        qa_type_info = QA_TYPES.get(qa_type, {})
        qa_type_name = qa_type_info.get("name", qa_type)

        messages = [
            {"role": "system", "content": reformatter_prompt.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": reformatter_prompt.USER_PROMPT.format(
                    TASK_ID=task,
                    QA_TYPE_ID=qa_type,
                    QA_TYPE_NAME=qa_type_name,
                    BASE_MCQS=json.dumps(base_qa, indent=2, ensure_ascii=False),
                ),
            },
        ]

        response = self.query_llm(messages)
        variants = self.fix_json(response)

        full_path = ""
        if save_response and variants is not None:
            out = os.path.join(output_dir, "qa_agent", task, qa_type, "reformatter")
            os.makedirs(out, exist_ok=True)
            safe_theme = theme.replace(" ", "_")
            full_path = os.path.join(out, f"{idx}_{safe_theme}.json")
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(variants, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Saved: '{full_path}'")

        return variants, full_path


# ==========================================
# QAAgent
# ==========================================
class QAAgent:
    def __init__(
        self,
        logger: logging.Logger,
        client_factory: LLMClientFactory,
        config: dict,
        distractor_pools: dict = None,
    ):
        self.logger = logger
        self.config = config
        self.distractor_pools = distractor_pools or {}   # {task: [{label, attributes}, ...]}
        self.qa_output = defaultdict(dict)             # {task: {qa_type: [[theme, base, path], ...]}}
        self.reformatted_output = defaultdict(dict)    # {task: {qa_type: [[theme, variants, path], ...]}}

        self.generator_cfg = config["qa_generator"]
        self.reformatter_cfg = config["reformatter"]

        self.generator = QAGenerator(
            logger=logger,
            client=client_factory.build(self.generator_cfg),
        )
        self.reformatter = Reformatter(
            logger=logger,
            client=client_factory.build(self.reformatter_cfg),
        )

    def run(self, task, theme, scene_graph, scenario, output_dir, idx, save_response=True):

        if task not in APPLICABILITY_MATRIX:
            self.logger.warning(f"[QAAgent] task {task!r} not in APPLICABILITY_MATRIX — skipping.")
            return

        applicable = APPLICABILITY_MATRIX[task]
        self.logger.info(
            f"#{idx} [QAAgent] task: '{task}' — {len(applicable)} applicable QA types"
        )

        pool = self.distractor_pools.get(task)

        for qa_type in sorted(applicable):  
            try:
                # 1) Generate base MCQ
                base_qa, base_path = self.generator.run(
                    task, qa_type, theme, scene_graph, scenario,
                    output_dir, idx,
                    distractor_pool=pool, save_response=save_response,
                )
                if base_qa is None:
                    continue
                self.qa_output[task].setdefault(qa_type, []).append(
                    [theme, base_qa, base_path]
                )




                # 2) Reformat into 3 variants
                ### 
                
                variants, var_path = self.reformatter.run(
                    task, qa_type, base_qa, theme,
                    output_dir, idx, save_response,
                )
                if variants is not None:
                    self.reformatted_output[task].setdefault(qa_type, []).append(
                        [theme, variants, var_path]
                    )
            except Exception as e:
                self.logger.error(
                    f"[QAAgent] error on (task={task}, qa_type={qa_type}, theme={theme}): {e}"
                )
