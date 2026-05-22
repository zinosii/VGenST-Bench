import argparse
import datetime
import json
import logging
import os
import time
from collections import defaultdict

from natsort import natsorted
from tqdm import tqdm

import utils.settings as defs
from utils.settings import TARGET_TASKS

from llm_client import LLMClientFactory
from media_client import MediaClientFactory


# ==========================================
# Logger
# ==========================================
def setup_logger(output_dir):
    log_file_path = os.path.join(output_dir, "pipeline.log")

    logger = logging.getLogger("VGenST_Pipeline")
    logger.setLevel(logging.INFO)
    logger.handlers = []

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(file_handler)

    class TqdmLoggingHandler(logging.Handler):
        def emit(self, record):
            tqdm.write(self.format(record))

    console_handler = TqdmLoggingHandler()
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)

    return logger


# ==========================================
# Config helpers
# ==========================================
def _to_bool(val):
    return str(val).lower() == "true"


def _resolve_theme_list(task):
    if task in {"MC_F_EGO_STA", "QC_F_EGO_DYN", "CI_F_EXO_STA"}:
        return getattr(defs, "THEMES_MC_F_EGO_STA", None)
    return getattr(defs, f"THEMES_{task}", None)


def _pick_latest_attempt(file_list, idx, safe_theme):
    candidates = [
        f for f in file_list
        if f.startswith(f"{idx}_{safe_theme}_") and f.endswith(".json")
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda x: int(x.replace(".json", "").split("_")[-1]))


def _load_run_outputs(base_dir, subfolder_name, target_tasks):
    output = defaultdict(list)
    for task in target_tasks:
        task_folder = os.path.join(base_dir, task, subfolder_name)
        if not os.path.exists(task_folder):
            continue

        file_list = [f for f in natsorted(os.listdir(task_folder)) if f.endswith(".json")]
        seen_keys = set()
        for filename in file_list:
            parts = filename.replace(".json", "").split("_")
            idx, safe_theme = parts[0], "_".join(parts[1:-1])
            key = (idx, safe_theme)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            latest = _pick_latest_attempt(file_list, idx, safe_theme)
            if latest is None:
                continue
            path = os.path.join(task_folder, latest)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            theme = safe_theme.replace("_", " ")
            output[task].append([theme, data, path])
    return output


# ==========================================
# Pipeline
# ==========================================
def run_pipeline(args):
    start_time = time.time()

    # ----- 0. Config -----
    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)

    overall = config["OVERALL"]
    providers_config = config["PROVIDERS"]

    if args.themes:
        mode = "custom"
        custom_themes = list(args.themes)
    else:
        mode = overall.get("mode", "benchmark").lower()
        custom_themes = list(overall.get("custom_themes", []))

    if mode not in {"benchmark", "custom"}:
        raise ValueError(f"Invalid OVERALL.mode: {mode!r} (expected 'benchmark' or 'custom')")
    if mode == "custom" and not custom_themes:
        raise ValueError(
            "mode='custom' requires themes via --themes or OVERALL.custom_themes in config."
        )

    running = overall["running_agents"]
    run_scene_graph = _to_bool(running.get("SCENE_GRAPH_AGENT"))
    run_scenario    = _to_bool(running.get("SCENARIO_AGENT"))
    run_video       = _to_bool(running.get("VIDEO_AGENT"))
    run_qa          = _to_bool(running.get("QA_AGENT"))
    resume_from     = running.get("RESUME_FROM")

    scene_graph_cfg = config["SCENE_GRAPH_AGENT"]
    scenario_cfg    = config["SCENARIO_AGENT"]
    video_cfg       = config["VIDEO_AGENT"]
    qa_cfg          = config["QA_AGENT"]

    image_model_info = config["IMAGE_MODELS"]
    video_model_info = config["VIDEO_MODELS"]

    # ----- Output / Logger -----
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("outputs", timestamp)
    os.makedirs(output_dir, exist_ok=True)
    logger = setup_logger(output_dir)

    logger.info(f"VGenST-Bench Started | Output Directory: {output_dir}")
    logger.info(f"Providers: {list(providers_config.keys())}")
    logger.info(f"Mode    : {mode}" + (f" | custom_themes={len(custom_themes)}" if mode == "custom" else ""))
    logger.info(
        "Agents  : "
        f"SCENE_GRAPH={run_scene_graph} | SCENARIO={run_scenario} | "
        f"VIDEO={run_video} | QA={run_qa}"
    )
    logger.info(f"Start   : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


    client_factory = LLMClientFactory(providers_config, logger)
    media_factory = MediaClientFactory(
        providers_config, image_model_info, video_model_info, logger
    )

    scene_graph_output = defaultdict(list)
    scenario_output = defaultdict(list)

    # ==========================================
    # 1. Scene Graph Agent
    # ==========================================
    if run_scene_graph:
        logger.info("=" * 40)
        logger.info(f"1. Scene Graph Agent")
        logger.info("=" * 40 + "\n")

        from agents.scene_graph_agent import SceneGraphAgent
        scene_graph_agent = SceneGraphAgent(logger, client_factory, scene_graph_cfg)
        
        if mode == "benchmark":
            for task in tqdm(TARGET_TASKS, desc="Tasks", position=0):
                theme_list = _resolve_theme_list(task)
                if theme_list is None:
                    logger.warning(f"THEMES_{task} not found in settings. Skipping.")
                    continue

                for idx, theme in enumerate(
                    tqdm(theme_list, desc=f"SceneGraph ({task})", leave=False, position=1)
                ):
                    
                    try:
                        scene_graph_agent.run(
                            theme, output_dir, idx, task=task, save_response=True
                        )
                    except Exception as e:
                        logger.error(f"Error in SceneGraph ({task}-{theme}): {e}")

        else:  # mode == "custom"
            for idx, theme in enumerate(
                tqdm(custom_themes, desc="SceneGraph (custom)", position=0)
            ):
                try:
                    scene_graph_agent.run(
                        theme, output_dir, idx, task=None, save_response=True
                    )
                except Exception as e:
                    logger.error(f"Error in SceneGraph (custom-{theme}): {e}")

        scene_graph_output = scene_graph_agent.scene_graph_output
    else:
        logger.info("Scene Graph Agent disabled — loading outputs from RESUME_FROM.")
        base = os.path.join("outputs", str(resume_from), "scene_graph_agent")
        scene_graph_output = _load_run_outputs(base, "scene_graph_generator", TARGET_TASKS)



    # ==========================================
    # 2. Scenario Agent
    # ==========================================
    if run_scenario:
        logger.info("=" * 40)
        logger.info("2. Scenario Agent")
        logger.info("=" * 40 + "\n")

        from agents.scenario_agent import ScenarioAgent
        scenario_agent = ScenarioAgent(logger, client_factory, scenario_cfg)

        for task, sg_list in tqdm(scene_graph_output.items(), desc="Tasks", position=0):
            for idx, (theme, scene_graph, path) in enumerate(
                tqdm(sg_list, desc=f"Scenario ({task})", leave=False, position=1)
            ):
                if not path:
                    continue
                try:
                    scenario_agent.run(
                        task, theme, scene_graph, output_dir, idx, save_response=True
                    )
                except Exception as e:
                    logger.error(f"Error in Scenario ({task}-{theme}): {e}")

        scenario_output = scenario_agent.scenario_output
    else:
        logger.info("Scenario Agent disabled — loading outputs from RESUME_FROM.")
        if not scene_graph_output:
            base_sg = os.path.join("outputs", str(resume_from), "scene_graph_agent")
            scene_graph_output = _load_run_outputs(base_sg, "scene_graph_generator", TARGET_TASKS)
        base_sc = os.path.join("outputs", str(resume_from), "scenario_agent")
        scenario_output = _load_run_outputs(base_sc, "scenario_generator", TARGET_TASKS)



    # ==========================================
    # 3. Video Agent
    # ==========================================
    if run_video:
        logger.info("=" * 40)
        logger.info("3. Video Agent")
        logger.info("=" * 40 + "\n")

        from agents.video_agent import VideoAgent
        video_agent = VideoAgent(
            logger, client_factory, media_factory, video_cfg
        )

        for task, sc_list in tqdm(scenario_output.items(), desc="Tasks", position=0):
            sg_map = {item[0]: item[1] for item in scene_graph_output.get(task, [])}

            for idx, (theme, scenario, path) in enumerate(
                tqdm(sc_list, desc=f"Video ({task})", leave=False, position=1)
            ):
                if not path:
                    continue
                try:
                    scene_graph = sg_map.get(theme)
                    
                    video_agent.run(
                        task, theme, scene_graph, scenario,
                        output_dir, idx, save_response=True,
                    )
                except Exception as e:
                    logger.error(f"Error in Video ({task}-{theme}): {e}")


    # ==========================================
    # 4. QA Agent
    # ==========================================
    if run_qa:
        logger.info("=" * 40)
        logger.info("4. QA Agent")
        logger.info("=" * 40 + "\n")

        distractor_pools = {}
        pools_root = os.path.join(
            os.path.dirname(__file__), "sysprompt", "qa_agent", "tasks"
        )
        for task in TARGET_TASKS:
            pool_path = os.path.join(pools_root, task, "distractor_pool.json")
            if not os.path.exists(pool_path):
                logger.warning(f"[QA] distractor pool missing for {task}: {pool_path}")
                continue
            with open(pool_path, "r", encoding="utf-8") as f:
                distractor_pools[task] = json.load(f)
        logger.info(f"[QA] loaded distractor pools for {len(distractor_pools)} tasks")

        from agents.qa_agent import QAAgent
        qa_agent = QAAgent(logger, client_factory, qa_cfg, distractor_pools=distractor_pools)

        for task, sc_list in tqdm(scenario_output.items(), desc="Tasks", position=0):
            sg_map = {item[0]: item[1] for item in scene_graph_output.get(task, [])}

            for idx, (theme, scenario, path) in enumerate(
                tqdm(sc_list, desc=f"QA ({task})", leave=False, position=1)
            ):
                if not path:
                    continue
                try:
                    scene_graph = sg_map.get(theme)
                    qa_agent.run(
                        task, theme, scene_graph, scenario,
                        output_dir, idx, save_response=True,
                    )
                except Exception as e:
                    logger.error(f"Error in QA ({task}-{theme}): {e}")

    # ==========================================
    # Done
    # ==========================================
    elapsed = str(datetime.timedelta(seconds=int(time.time() - start_time)))
    logger.info("=" * 40)
    logger.info("Pipeline Completed.")
    logger.info(f"Total Execution Time: {elapsed}")
    logger.info(f"Logs: {os.path.join(output_dir, 'pipeline.log')}")
    logger.info("=" * 40)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run VGenST-Bench pipeline")
    parser.add_argument(
        "--config", type=str,
        default=os.path.join(os.path.dirname(__file__), "config.json"),
        help="Path to VGenST config file",
    )
    parser.add_argument(
        "--themes", nargs="+", default=None,
        help="Custom themes (overrides OVERALL.custom_themes). Implies mode='custom'.",
    )
    args = parser.parse_args()
    run_pipeline(args)
