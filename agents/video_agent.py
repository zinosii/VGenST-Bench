import importlib
import json
import logging
import os
from collections import defaultdict

from .base_agent import BaseAgent
from ._examples import load_examples, format_examples
from llm_client import LLMClientFactory
from media_client import MediaClientFactory, MediaClient

from sysprompt.video_agent import image_prompt_translator as image_prompt_translator_prompt
from sysprompt.video_agent import video_prompt_translator as video_prompt_translator_prompt


_IMG_EXAMPLES_DIR = os.path.join(
    os.path.dirname(__file__), "..",
    "sysprompt", "video_agent", "examples", "image_prompt_translator",
)
_VID_EXAMPLES_DIR = os.path.join(
    os.path.dirname(__file__), "..",
    "sysprompt", "video_agent", "examples", "video_prompt_translator",
)


# ==========================================
# ImagePromptTranslator (LLM)
# ==========================================
class ImagePromptTranslator(BaseAgent):
    def __init__(self, logger, client):
        super().__init__(logger, client)
        self._examples = load_examples(_IMG_EXAMPLES_DIR)

    def _example_for(self, task) -> str:
        return format_examples(self._examples.get(task) or [])

    def run(self, task, theme, scene_graph, scenario, output_dir, idx, save_response=True):
        self.logger.info(
            f"#{idx} [ImagePromptTranslator] task: '{task}' theme: '{theme}' ..."
        )

        folder_name = task.split("_", 1)[1]
        module_path = f"sysprompt.scene_graph_agent.{folder_name}.{task}"
        module = importlib.import_module(module_path)

        TASK_DEFINITION = getattr(module, "TASK_DEFINITION")
        TASK_RULES = getattr(module, "TASK_RULES")
        TASK_GUIDELINES = getattr(module, "TASK_GUIDELINES")
        
        messages = [
            {"role": "system", "content": image_prompt_translator_prompt.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": image_prompt_translator_prompt.USER_PROMPT.format(
                    SCENE_GRAPH=scene_graph,
                    TASK_DEFINITION=TASK_DEFINITION,
                    TASK_RULES=TASK_RULES,
                    TASK_GUIDELINES=TASK_GUIDELINES,
                    SCENARIO=scenario,
                    EXAMPLE=self._example_for(task),
                ),
            },
        ]
        
        ## HARDCODED for QC_F_EGO_DYN
        if task == "QC_F_EGO_DYN":
            if not (idx // 10) % 2 == 0:
                messages[1]["content"] = messages[1]["content"].replace(
                    "To the left of the container",
                    "To the right of the container",
                )

        response = self.query_llm(messages)
        image_prompt = self.fix_json(response)

        full_path = ""
        if save_response and image_prompt is not None:
            out = os.path.join(output_dir, "video_agent", task, "image_prompt_translator")
            os.makedirs(out, exist_ok=True)
            safe_theme = theme.replace(" ", "_")
            full_path = os.path.join(out, f"{idx}_{safe_theme}.json")
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(image_prompt, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Saved: '{full_path}'")

        return image_prompt, full_path


# ==========================================
# VideoPromptTranslator (LLM)
# ==========================================
class VideoPromptTranslator(BaseAgent):
    def __init__(self, logger, client):
        super().__init__(logger, client)
        self._examples = load_examples(_VID_EXAMPLES_DIR)

    def _example_for(self, task) -> str:
        return format_examples(self._examples.get(task) or [])

    def run(self, task, theme, scene_graph, scenario, output_dir, idx, save_response=True):
        self.logger.info(
            f"#{idx} [VideoPromptTranslator] task: '{task}' theme: '{theme}' ..."
        )

        folder_name = task.split("_", 1)[1]
        module_path = f"sysprompt.scene_graph_agent.{folder_name}.{task}"
        module = importlib.import_module(module_path)

        TASK_DEFINITION = getattr(module, "TASK_DEFINITION")
        TASK_RULES = getattr(module, "TASK_RULES")
        TASK_GUIDELINES = getattr(module, "TASK_GUIDELINES")

        messages = [
            {"role": "system", "content": video_prompt_translator_prompt.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": video_prompt_translator_prompt.USER_PROMPT.format(
                    SCENE_GRAPH=scene_graph,
                    TASK_DEFINITION=TASK_DEFINITION,
                    TASK_RULES=TASK_RULES,
                    TASK_GUIDELINES=TASK_GUIDELINES,
                    SCENARIO=scenario,
                    EXAMPLE=self._example_for(task),
                ),
            },
        ]
        

        response = self.query_llm(messages)
        video_prompt = self.fix_json(response)

        ## EXCEPTION for BT_E_EXO_DYN - I2V prompt -> T2V prompt
        if task == "BT_E_EXO_DYN":
            video_prompt = video_prompt.replace("Continuing from the anchor frame.", "")

        full_path = ""
        if save_response and video_prompt is not None:
            out = os.path.join(output_dir, "video_agent", task, "video_prompt_translator")
            os.makedirs(out, exist_ok=True)
            safe_theme = theme.replace(" ", "_")
            full_path = os.path.join(out, f"{idx}_{safe_theme}.json")
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(video_prompt, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Saved: '{full_path}'")

        return video_prompt, full_path


# ==========================================
# ImageGenerator (MediaClient)
# ==========================================
class ImageGenerator:
    def __init__(self, logger, media_client: MediaClient, image_model: str):
        self.logger = logger
        self.media_client = media_client
        self.image_model = image_model

    def run(self, task, theme, image_prompt, output_dir, idx, save_response=True):
        self.logger.info(
            f"#{idx} [ImageGenerator] task: '{task}' theme: '{theme}' model={self.image_model}"
        )
        out = os.path.join(output_dir, "video_agent", task, "image_generator")
        safe_theme = theme.replace(" ", "_")
        save_path = os.path.join(out, f"{idx}_{safe_theme}.png")

        path = self.media_client.generate_image(
            image_prompt=image_prompt,
            image_model=self.image_model,
            save_path=save_path,
        )
        return path  # None on failure


# ==========================================
# VideoGenerator (MediaClient)
# ==========================================
class VideoGenerator:
    def __init__(self, logger, media_client: MediaClient, video_model: str):
        self.logger = logger
        self.media_client = media_client
        self.video_model = video_model

    def run(self, task, theme, video_prompt, first_frame_path, output_dir, idx, save_response=True):
        self.logger.info(
            f"#{idx} [VideoGenerator] task: '{task}' theme: '{theme}' model={self.video_model}"
        )
        
        # EXCEPTION for BT_E_EXO_DYN - first_frame_path is not used, so skip existence check
        if task != "BT_E_EXO_DYN":
            if not first_frame_path or not os.path.exists(first_frame_path):
                self.logger.error(f"[VideoGenerator] first_frame not found: {first_frame_path}")
                return None

        out = os.path.join(output_dir, "video_agent", task, "video_generator")
        safe_theme = theme.replace(" ", "_")
        save_path = os.path.join(out, f"{idx}_{safe_theme}.mp4")

        prompt_str = (
            video_prompt["prompt"] if isinstance(video_prompt, dict) and "prompt" in video_prompt
            else str(video_prompt)
        )

        path = self.media_client.generate_video(
            video_prompt=prompt_str,
            first_frame_path=first_frame_path,
            video_model=self.video_model,
            save_path=save_path,
        )
        return path  # None on failure


# ==========================================
# VideoAgent
# ==========================================
class VideoAgent:
    def __init__(
        self,
        logger: logging.Logger,
        client_factory: LLMClientFactory,
        media_factory: MediaClientFactory,
        config: dict,
    ):
        self.logger = logger
        self.config = config

        self.image_prompt_output = defaultdict(list)
        self.image_output = defaultdict(list)
        self.video_prompt_output = defaultdict(list)
        self.video_output = defaultdict(list)

        ipt_cfg = config["image_prompt_translator"]
        ig_cfg = config["image_generator"]
        vpt_cfg = config["video_prompt_translator"]
        vg_cfg = config["video_generator"]

        self.image_prompt_translator = ImagePromptTranslator(
            logger=logger, client=client_factory.build(ipt_cfg),
        )
        self.video_prompt_translator = VideoPromptTranslator(
            logger=logger, client=client_factory.build(vpt_cfg),
        )

        self.image_generator = ImageGenerator(
            logger=logger,
            media_client=media_factory.build(ig_cfg),
            image_model=ig_cfg["image_model"],
        )
        self.video_generator = VideoGenerator(
            logger=logger,
            media_client=media_factory.build(vg_cfg),
            video_model=vg_cfg["video_model"],
        )

    def run(self, task, theme, scene_graph, scenario, output_dir, idx, save_response=True):
        result = {
            "image_prompt": None, "image_prompt_path": None,
            "image_path": None,
            "video_prompt": None, "video_prompt_path": None,
            "video_path": None,
        }

        # 1) image prompt
        image_prompt, image_prompt_path = self.image_prompt_translator.run(
            task, theme, scene_graph, scenario, output_dir, idx, save_response
        )
        if image_prompt is None:
            self.logger.warning(f"#{idx} image prompt failed — skipping rest.")
            return result
        result["image_prompt"] = image_prompt
        result["image_prompt_path"] = image_prompt_path
        self.image_prompt_output[task].append([theme, image_prompt, image_prompt_path])

        # 2) image
        image_path = self.image_generator.run(
            task, theme, image_prompt, output_dir, idx, save_response
        )
        if image_path is None:
            self.logger.warning(f"#{idx} image generation failed — skipping rest.")
            return result
        result["image_path"] = image_path
        self.image_output[task].append([theme, image_path])
        
        # 3) video prompt
        video_prompt, video_prompt_path = self.video_prompt_translator.run(
            task, theme, scene_graph, scenario, output_dir, idx, save_response
        )
        if video_prompt is None:
            self.logger.warning(f"#{idx} video prompt failed — skipping rest.")
            return result
        result["video_prompt"] = video_prompt
        result["video_prompt_path"] = video_prompt_path
        self.video_prompt_output[task].append([theme, video_prompt, video_prompt_path])

        # 4) video
        video_path = self.video_generator.run(
            task, theme, video_prompt, image_path, output_dir, idx, save_response
        )
        if video_path is None:
            self.logger.warning(f"#{idx} video generation failed.")
            return result
        result["video_path"] = video_path
        self.video_output[task].append([theme, video_path])

        return result
