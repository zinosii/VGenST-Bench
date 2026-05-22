import argparse
import datetime
import glob
import json
import logging
import os
import re
import sys
from collections import defaultdict
from typing import Optional

import pandas as pd
from tqdm import tqdm

from llm_client import LLMClientFactory
from sysprompt.qa_agent.applicability_matrix import APPLICABILITY_MATRIX, QA_TYPES


# ==========================================
# Constants
# ==========================================

VARIANT_KEYS = {
    "base": "base",
    "v1": "variant_NoT_distractor",
    "v2": "variant_NoT_answer",
    "v3": "variant_open_ended",
}
VARIANT_LIST = ["base", "v1", "v2", "v3"]

DEFAULT_EVAL_CONFIG = os.path.join(os.path.dirname(__file__), "eval_config.json")
DEFAULT_PIPELINE_CONFIG = os.path.join(os.path.dirname(__file__), "config.json")



SYSTEM_MCQ = """You are answering a multiple-choice question about a video scene.
Respond with ONLY the letter of the correct option (A, B, C, ...). No explanation, no extra text."""


SYSTEM_OE = """You are answering an open-ended question about a video scene.
Respond concisely. No explanation."""

USER_VIDEO_CONTEXT = """[QUESTION]
{question}

Answer:"""

JUDGE_SYSTEM = """You are a strict judge for benchmark answers.

Given:
  - Expected answer (ground truth)
  - Model's response (free-form)

Decide if the response is semantically equivalent to the expected answer.
Be generous. If response and expected have same meaning, thenk the response is correct. 

Output JSON only, no prose:
{"correct": true|false, "reason": "<one short sentence>"}"""

JUDGE_USER = """Expected: {expected}
Response: {response}

Is the response correct?"""



# ==========================================
# Eval-config loading (eval_config.json)
# ==========================================
def load_eval_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    for key in ("DATA", "TARGET", "EVAL_MODES", "RUN"):
        if key not in cfg:
            raise ValueError(f"eval_config.json missing required section: {key!r}")
    return cfg


# ==========================================
# Logger
# ==========================================
def setup_logger():
    logger = logging.getLogger("VGenST_Eval")
    logger.setLevel(logging.INFO)
    logger.handlers = []

    class TqdmLoggingHandler(logging.Handler):
        def emit(self, record):
            tqdm.write(self.format(record))

    h = TqdmLoggingHandler()
    h.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(h)
    return logger


# ==========================================
# Loading helpers 
# ==========================================
def find_video_path(data_root: str, task: str, safe_theme_with_idx: str) -> Optional[str]:
    path = os.path.join(data_root, "videos", task, "videos", f"{safe_theme_with_idx}.mp4")
    return path if os.path.exists(path) else None


def find_frames_dir(data_root: str, task: str, safe_theme_with_idx: str) -> Optional[str]:
    """{data_root}/videos/{task}/processed_frames/{idx}_{safe_theme}/"""
    path = os.path.join(data_root, "videos", task, "processed_frames", safe_theme_with_idx)
    return path if os.path.isdir(path) else None


def find_first_frame_path(data_root: str, task: str, safe_theme_with_idx: str) -> Optional[str]:
    path = os.path.join(data_root, "videos", task, "first_frame", f"{safe_theme_with_idx}.png")
    return path if os.path.exists(path) else None


def list_frames(frames_dir: Optional[str]) -> list:
    if not frames_dir:
        return []
    paths = []
    for ext in ("png", "jpg", "jpeg"):
        paths.extend(glob.glob(os.path.join(frames_dir, f"frame_*.{ext}")))
    return sorted(paths)


def _clean_variant(v):
    if not isinstance(v, dict):
        return v
    out = dict(v)
    if isinstance(out.get("options"), dict):
        out["options"] = {k: vv for k, vv in out["options"].items() if vv is not None}
    return out


def iter_qa_items(data_root: str, task_filter: Optional[str] = None,
                   qa_type_filter: Optional[str] = None):
    pattern = os.path.join(data_root, "qa", "*.parquet")
    for parquet_path in sorted(glob.glob(pattern)):
        task = os.path.splitext(os.path.basename(parquet_path))[0]
        if task_filter and task != task_filter:
            continue

        df = pd.read_parquet(parquet_path)
        for _, row in df.iterrows():
            qa_type = row["qa_type"]
            if qa_type_filter and qa_type != qa_type_filter:
                continue

            idx = int(row["idx"])
            safe_theme = str(row["theme"])
            theme = safe_theme.replace("_", " ")
            safe_theme_with_idx = f"{idx}_{safe_theme}"
            sample_id = row["sample_id"]

            video_path = find_video_path(data_root, task, safe_theme_with_idx)
            frames_dir = find_frames_dir(data_root, task, safe_theme_with_idx)
            first_frame = find_first_frame_path(data_root, task, safe_theme_with_idx)

            yield {
                "task": task, "qa_type": qa_type,
                "theme": theme, "idx": idx,
                "safe_theme": safe_theme,
                "safe_theme_with_idx": safe_theme_with_idx,
                "sample_id": sample_id,
                "video_path": video_path,
                "frames_dir": frames_dir,
                "first_frame": first_frame,
                "n_frames": len(list_frames(frames_dir)),
                "base": _clean_variant(row.get("base")),
                "v1":   _clean_variant(row.get("variant_NoT_distractor")),
                "v2":   _clean_variant(row.get("variant_NoT_answer")),
                "v3":   _clean_variant(row.get("variant_open_ended")),
            }


# ==========================================
# Variant -> (kind, question, ground_truth)
# ==========================================
def variant_to_query(item: dict, vkey: str):
    """
    Returns (kind, question_text, ground_truth) or None if variant is rejected/missing.
    kind: "mcq" or "oe"
    """
    v = item.get(vkey)
    if v is None:
        return None
    if vkey == "v3":
        return "oe", v["question"], v["expected_answer"]
    # base / v1 / v2 are all MCQ
    return "mcq", v["question"], v["answer"]


# ==========================================
# MCQ response parser
# ==========================================
_MCQ_LETTER_RE = re.compile(r"\b([A-Z])\b")


def parse_mcq_letter(response: str) -> Optional[str]:
    if not response:
        return None
    m = _MCQ_LETTER_RE.search(response.strip())
    return m.group(1) if m else None


# ==========================================
# Circular eval helpers
# ==========================================
def extract_stem(question: str, options: dict) -> str:
    letters = sorted(options.keys())
    if not letters:
        return question
    first = letters[0]
    first_text = options[first]
    # exact match: "A. <text>"
    marker = f"{first}. {first_text}"
    pos = question.find(marker)
    if pos > 0:
        return question[:pos].rstrip(": ").rstrip()
    # fallback regex: "[\s:]+A.\s+"
    m = re.search(rf"[\s:]+{re.escape(first)}\.\s+", question)
    if m:
        return question[:m.start()].rstrip(": ").rstrip()
    return question


def build_circular_variants(stem: str, options: dict, original_answer: str):
    letters = sorted(options.keys())
    if original_answer not in options:
        return

    for target_letter in letters:
        new_options = dict(options)
        if target_letter != original_answer:
            new_options[original_answer] = options[target_letter]
            new_options[target_letter] = options[original_answer]
        opts_str = ", ".join(f"{L}. {new_options[L]}" for L in letters)
        new_question = f"{stem}: {opts_str}"
        yield target_letter, new_question, new_options


# ==========================================
# Multi-image (frames) call helpers
# ==========================================
import base64


def _encode_image_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def _media_type_from_path(path: str) -> str:
    ext = path.rsplit(".", 1)[-1].lower()
    return "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"


def _claude_frames_chat(client, system_text, question_text, frame_paths) -> Optional[str]:
    """Claude messages.create with image blocks + text."""
    blocks = []
    for p in frame_paths:
        blocks.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": _media_type_from_path(p),
                "data": _encode_image_b64(p),
            },
        })
    blocks.append({"type": "text", "text": question_text})
    resp = client.client.messages.create(
        model=client.model,
        system=system_text or None,
        messages=[{"role": "user", "content": blocks}],
        max_tokens=client.max_tokens,
    )
    return resp.content[0].text


def _openai_frames_chat(client, system_text, question_text, frame_paths) -> Optional[str]:
    """OpenAI / vLLM (OpenAI-compatible) chat.completions with image_url content."""
    content = []
    for p in frame_paths:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{_media_type_from_path(p)};base64,{_encode_image_b64(p)}"},
        })
    content.append({"type": "text", "text": question_text})

    kwargs = {
        "model": client.model,
        "messages": [
            {"role": "system", "content": system_text},
            {"role": "user", "content": content},
        ],
    }
    if client.base_url:
        kwargs["max_tokens"] = client.max_tokens
    else:
        kwargs["max_completion_tokens"] = client.max_tokens

    resp = client.client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content


def _gemini_frames_chat(client, system_text, question_text, frame_paths) -> Optional[str]:
    """Gemini multimodal via google-genai SDK (Part.from_bytes)."""
    from google.genai import types as gem_types
    parts = []
    for p in frame_paths:
        with open(p, "rb") as f:
            parts.append(
                gem_types.Part.from_bytes(data=f.read(), mime_type=_media_type_from_path(p))
            )
    parts.append(question_text)

    resp = client.client.models.generate_content(
        model=client.model,
        contents=parts,
        config={
            "system_instruction": system_text,
            "max_output_tokens": client.max_tokens,
        },
    )
    return resp.text


def call_target_with_frames(target_client, provider, system_text, question_text, frame_paths
                              ) -> Optional[str]:
    try:
        if provider == "claude":
            return _claude_frames_chat(target_client, system_text, question_text, frame_paths)
        if provider in ("openai", "vllm"):
            return _openai_frames_chat(target_client, system_text, question_text, frame_paths)
        if provider == "gemini":
            return _gemini_frames_chat(target_client, system_text, question_text, frame_paths)
        raise NotImplementedError(f"frames-eval not implemented for provider {provider!r}")
    except Exception as e:
        target_client.logger.error(f"[call_target_with_frames] {e}")
        return None


# ==========================================
# Judge (LLM-as-judge for OE)
# ==========================================
def judge_oe(judge_client, expected: str, response: str) -> dict:
    """Returns {correct: bool, reason: str}."""
    if not response:
        return {"correct": False, "reason": "empty response"}

    user_text = JUDGE_USER.format(expected=expected, response=response)
    cls = judge_client.__class__.__name__
    
    
    #######TEST
    # return {"correct": True, "reason": " correct"}

    if cls == "ClaudeClient":
        resp = judge_client.client.messages.create(
            model=judge_client.model,
            system=JUDGE_SYSTEM,
            messages=[{"role": "user", "content": user_text}],
            max_tokens=judge_client.max_tokens,
        )
        raw = resp.content[0].text
    elif cls == "GeminiClient":
        resp = judge_client.client.models.generate_content(
            model=judge_client.model,
            contents=[user_text],
            config={
                "system_instruction": JUDGE_SYSTEM,
                "temperature": judge_client.temperature,
                "max_output_tokens": judge_client.max_tokens,
            },
        )
        raw = resp.text
    else:
        messages = [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": user_text},
        ]
        judge_kwargs = {
            "model": judge_client.model,
            "messages": messages,
            "temperature": judge_client.temperature,
        }
        if getattr(judge_client, "base_url", None):
            judge_kwargs["max_tokens"] = judge_client.max_tokens
        else:
            judge_kwargs["max_completion_tokens"] = judge_client.max_tokens
        resp = judge_client.client.chat.completions.create(**judge_kwargs)
        raw = resp.choices[0].message.content

    if not raw:
        return {"correct": False, "reason": "judge call failed"}
    # Light-weight JSON extraction
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return {"correct": False, "reason": f"judge non-JSON: {raw[:80]}"}
    try:
        parsed = json.loads(m.group(0))
        return {
            "correct": bool(parsed.get("correct")),
            "reason": str(parsed.get("reason", "")),
        }
    except Exception:
        return {"correct": False, "reason": f"judge JSON parse fail: {raw[:80]}"}


# ==========================================
# Circular eval — N positions per base MCQ
# ==========================================
def call_target(target_client, provider, system_text, question_text, ctx_payload):
    user_text = USER_VIDEO_CONTEXT.format(question=question_text)
    return call_target_with_frames(
        target_client, provider, system_text, user_text, ctx_payload["frame_paths"]
    )


def eval_circular_one(target_client, provider, item, ctx_payload):
    base = item["base"]
    options = base["options"]
    original_answer = base["answer"]
    stem = extract_stem(base["question"], options)

    per_position = []
    n_correct = 0
    for target_letter, new_question, new_options in build_circular_variants(
        stem, options, original_answer
    ):
        response_raw = call_target(target_client, provider, SYSTEM_MCQ, new_question, ctx_payload)
        parsed = parse_mcq_letter(response_raw)
        correct = (parsed == target_letter)
        if correct:
            n_correct += 1
        per_position.append({
            "position": target_letter,
            "question": new_question,
            "options": new_options,
            "response_raw": response_raw,
            "response_parsed": parsed,
            "correct": correct,
        })

    n_positions = len(per_position)
    all_correct = (n_positions > 0 and n_correct == n_positions)

    return {
        "eval_mode": "circular_base",
        "task": item["task"],
        "qa_type": item["qa_type"],
        "theme": item["theme"],
        "idx": item["idx"],
        "variant": "base_circular",
        "kind": "mcq",
        "stem": stem,
        "original_answer": original_answer,
        "n_positions": n_positions,
        "n_correct_positions": n_correct,
        "per_position": per_position,
        "all_correct": all_correct,
        "correct": all_correct,   # for aggregation compatibility
    }


# ==========================================
# Aggregation
# ==========================================
def _macro_over_qa(records_subset: list) -> float:
    if not records_subset:
        return 0.0
    by_qt = defaultdict(lambda: {"n": 0, "correct": 0})
    for r in records_subset:
        by_qt[r["qa_type"]]["n"] += 1
        if r.get("correct"):
            by_qt[r["qa_type"]]["correct"] += 1
    accs = [v["correct"] / v["n"] for v in by_qt.values() if v["n"] > 0]
    return sum(accs) / len(accs) if accs else 0.0


def _bucket(records: list, key_fn) -> dict:
    out = defaultdict(list)
    for r in records:
        out[key_fn(r)].append(r)
    return out


def aggregate(records: list) -> dict:
    summary = {
        "total": len(records),
        "correct": sum(1 for r in records if r["correct"]),
        "by_variant": defaultdict(lambda: {"n": 0, "correct": 0}),
        "by_task": defaultdict(lambda: {"n": 0, "correct": 0}),
        "by_qa_type": defaultdict(lambda: {"n": 0, "correct": 0}),
        "by_level": defaultdict(lambda: {"n": 0, "correct": 0}),
        "by_scale": defaultdict(lambda: {"n": 0, "correct": 0}),
    }

    def _level_of(r):
        return r["qa_type"].split("-", 1)[0] if "-" in r.get("qa_type", "") else "unknown"

    for r in records:
        ok = 1 if r["correct"] else 0

        def bump(d, k):
            d[k]["n"] += 1
            d[k]["correct"] += ok

        bump(summary["by_variant"], r["variant"])
        bump(summary["by_task"], r["task"])
        bump(summary["by_qa_type"], r["qa_type"])
        bump(summary["by_level"], _level_of(r))
        # Scale = 2nd token of task code (e.g., F/V/E)
        scale = r["task"].split("_")[1] if "_" in r["task"] else "unknown"
        bump(summary["by_scale"], scale)

    # Compute accuracy (micro)
    summary["overall_accuracy"] = (
        summary["correct"] / summary["total"] if summary["total"] else 0
    )
    for d in (summary["by_variant"], summary["by_task"],
              summary["by_qa_type"], summary["by_level"], summary["by_scale"]):
        for k, v in d.items():
            v["accuracy"] = v["correct"] / v["n"] if v["n"] else 0

    # Convert defaultdicts → regular dicts
    for k in ("by_variant", "by_task", "by_qa_type", "by_level", "by_scale"):
        summary[k] = dict(summary[k])

    # ----- Cross-tabs (task × eval_mode) -----
    by_t_e_micro = {}   # {task: {mode: {n, correct, accuracy}}}
    by_t_e_macro = {}   # {task: {mode: macro_acc_over_qa_types}}
    for task, recs_t in _bucket(records, lambda r: r["task"]).items():
        by_t_e_micro[task] = {}
        by_t_e_macro[task] = {}
        for mode, recs_tm in _bucket(recs_t, lambda r: r.get("eval_mode", "?")).items():
            n = len(recs_tm)
            c = sum(1 for r in recs_tm if r.get("correct"))
            by_t_e_micro[task][mode] = {"n": n, "correct": c, "accuracy": c / n if n else 0}
            by_t_e_macro[task][mode] = _macro_over_qa(recs_tm)
    summary["by_task_x_eval_mode"] = by_t_e_micro
    summary["by_task_x_eval_mode_macro"] = by_t_e_macro

    # ----- Cross-tabs (level × eval_mode), macro over qa_types within level -----
    by_l_e_micro = {}
    by_l_e_macro = {}
    for lvl, recs_l in _bucket(records, _level_of).items():
        by_l_e_micro[lvl] = {}
        by_l_e_macro[lvl] = {}
        for mode, recs_lm in _bucket(recs_l, lambda r: r.get("eval_mode", "?")).items():
            n = len(recs_lm)
            c = sum(1 for r in recs_lm if r.get("correct"))
            by_l_e_micro[lvl][mode] = {"n": n, "correct": c, "accuracy": c / n if n else 0}
            by_l_e_macro[lvl][mode] = _macro_over_qa(recs_lm)
    summary["by_level_x_eval_mode"] = by_l_e_micro
    summary["by_level_x_eval_mode_macro"] = by_l_e_macro

    # ----- Per-task macro acc over qa_types (mode-agnostic) -----
    summary["by_task_macro"] = {
        task: _macro_over_qa(recs)
        for task, recs in _bucket(records, lambda r: r["task"]).items()
    }
    summary["by_level_macro"] = {
        lvl: _macro_over_qa(recs)
        for lvl, recs in _bucket(records, _level_of).items()
    }

    return summary


# ==========================================
# Main
# ==========================================
def _resolve_run_options(args, eval_cfg) -> dict:
    data_cfg = eval_cfg["DATA"]
    target_cfg = eval_cfg["TARGET"]
    run_cfg = eval_cfg["RUN"]

    return {
        "data_root":      args.data_root or data_cfg["data_root"],
        "out_dir":        args.out_dir or data_cfg["out_dir"],
        "model":          args.model or target_cfg["model"],
        "model_alias":    args.model_alias or target_cfg["model_alias"],
        "judge_provider": args.judge_provider or target_cfg.get("judge_provider") or (args.model or target_cfg["model"]),
        "judge_alias":    target_cfg.get("judge_alias", "fast"),
        "selected_modes":  _parse_modes(args.modes, run_cfg["selected_modes"]),
        "task":            args.task if args.task is not None else run_cfg.get("task"),
        "qa_type":         args.qa_type if args.qa_type is not None else run_cfg.get("qa_type"),
        "limit":           args.limit if args.limit else run_cfg.get("limit", 0),
        "per_task_limit":  args.per_task_limit if args.per_task_limit else run_cfg.get("per_task_limit", 0),
        "tag":             args.tag if args.tag else run_cfg.get("tag", ""),
    }


def _parse_modes(cli_modes, cfg_default):
    if cli_modes:
        return [s.strip() for s in cli_modes.split(",") if s.strip()]
    return [str(m) for m in cfg_default]


def run_eval(args):
    logger = setup_logger()

    # ----- Load configs -----
    with open(args.config, "r", encoding="utf-8") as f:
        pipeline_cfg = json.load(f)
    providers = pipeline_cfg["PROVIDERS"]

    eval_cfg = load_eval_config(args.eval_config)
    eval_modes_dict = eval_cfg["EVAL_MODES"]

    opts = _resolve_run_options(args, eval_cfg)

    # ----- Validate selected modes -----
    invalid = [s for s in opts["selected_modes"] if s not in eval_modes_dict]
    if invalid:
        raise ValueError(
            f"Invalid eval-mode key(s) {invalid}. "
            f"Allowed: {list(eval_modes_dict.keys())} "
            f"→ {[m['name'] for m in eval_modes_dict.values()]}"
        )
    selected_names = [eval_modes_dict[s]["name"] for s in opts["selected_modes"]]

    # ----- Build clients -----
    if opts["model"] not in providers:
        logger.error(f"model {opts['model']!r} not in PROVIDERS. Available: {list(providers)}")
        sys.exit(1)
    factory = LLMClientFactory(providers, logger)
    
    
    
    
    target_client = factory.build({
        "provider": opts["model"],
        "model": opts["model_alias"],
        "temperature": 0.7,
        "max_tokens": 8192,
    })
    
    
    
    judge_client = factory.build({
        "provider": opts["judge_provider"],
        "model": opts["judge_alias"],
        "temperature": 0.0,
        "max_tokens": 8192,
    })






    logger.info(f"Eval cfg  : {args.eval_config}")
    logger.info(f"Target    : {opts['model']} (model={target_client.model})")
    logger.info(f"Judge     : {opts['judge_provider']} (model={judge_client.model})")
    logger.info(f"Input     : processed_frames (multi-image)")
    logger.info(f"Data root : {opts['data_root']}")
    logger.info(f"Eval modes: {opts['selected_modes']} → {selected_names}")

    # ----- Output paths -----
    eval_tag = opts["model"]
    if len(opts["selected_modes"]) == 1:
        eval_tag += f"_{selected_names[0]}"
    else:
        eval_tag += f"_modes-{'+'.join(opts['selected_modes'])}"
    if opts["tag"]:
        eval_tag += f"_{opts['tag']}"
    eval_tag += f"_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out_dir = os.path.join(opts["out_dir"], eval_tag)
    os.makedirs(out_dir, exist_ok=True)
    perq_path = os.path.join(out_dir, "per_question.jsonl")
    sum_path = os.path.join(out_dir, "summary.json")

    logger.info(f"Output    : {out_dir}\n")

    # ----- Iterate -----
    records = []
    items = list(iter_qa_items(opts["data_root"], opts["task"], opts["qa_type"]))

    if opts["per_task_limit"]:
        
        

        keep_per_task = defaultdict(set)
        filtered = []
        for it in items:
            sid_set = keep_per_task[it["task"]]
            if it["sample_id"] in sid_set:
                filtered.append(it)
            elif len(sid_set) < opts["per_task_limit"]:
                sid_set.add(it["sample_id"])
                filtered.append(it)
        items = filtered

    if opts["limit"]:
        items = items[: opts["limit"]]
    n_unique_samples = len({(it["task"], it["sample_id"]) for it in items})
    
    
    
    logger.info(
        f"Loaded {len(items)} QA rows ({n_unique_samples} unique samples"
        + (f", per_task_limit={opts['per_task_limit']}" if opts["per_task_limit"] else "")
        + ")\n"
    )

    perq_f = open(perq_path, "w", encoding="utf-8")

    try:
        for item in tqdm(items, desc="Items", position=0):
            frames_dir = item["frames_dir"]
            if not frames_dir:
                logger.warning(
                    f"[skip] no frames dir for {item['task']}/{item['safe_theme_with_idx']}"
                )
                continue
            frame_paths = list_frames(frames_dir)
            if not frame_paths:
                logger.warning(
                    f"[skip] frames dir empty: {frames_dir}"
                )
                continue
            ctx_payload = {"frame_paths": frame_paths}
         
            
            


            for mkey in opts["selected_modes"]:
                mode = eval_modes_dict[mkey]
                vkey = mode["variant"]

                # === Circular eval branch ===
                if mode["circular"]:
                    if item["base"] is None:
                        continue
                    rec = eval_circular_one(target_client, opts["model"], item, ctx_payload)
                    rec["eval_mode"] = mode["name"]
                    records.append(rec)
                    perq_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    perq_f.flush()
                    continue

                # === Standard variant branch ===
                q = variant_to_query(item, vkey)
                if q is None:
                    continue
                kind, question_text, gt = q

                system_text = SYSTEM_MCQ if kind == "mcq" else SYSTEM_OE
                response_raw = call_target(
                    target_client, opts["model"], system_text, question_text, ctx_payload
                )

                # Score
                if kind == "mcq":
                    parsed = parse_mcq_letter(response_raw)
                    correct = (parsed == gt) if parsed else False
                    judge_reason = None
                else:
                    j = judge_oe(judge_client, gt, response_raw or "")
                    correct = j["correct"]
                    parsed = response_raw
                    judge_reason = j["reason"]

                rec = {
                    "eval_mode": mode["name"],
                    "task": item["task"],
                    "qa_type": item["qa_type"],
                    "theme": item["theme"],
                    "idx": item["idx"],
                    "variant": vkey,
                    "kind": kind,
                    "question": question_text,
                    "ground_truth": gt,
                    "response_raw": response_raw,
                    "response_parsed": parsed,
                    "correct": correct,
                    "judge_reason": judge_reason,
                }
                records.append(rec)
                perq_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                perq_f.flush()
    finally:
        perq_f.close()

    # ----- Summary -----
    summary = aggregate(records)
    summary["model"] = opts["model"]
    summary["model_id"] = target_client.model
    summary["eval_modes"] = selected_names
    summary["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    by_eval_mode = defaultdict(lambda: {"n": 0, "correct": 0})
    for r in records:
        em = r.get("eval_mode", "?")
        by_eval_mode[em]["n"] += 1
        if r.get("correct"):
            by_eval_mode[em]["correct"] += 1
    for v in by_eval_mode.values():
        v["accuracy"] = v["correct"] / v["n"] if v["n"] else 0
    summary["by_eval_mode"] = dict(by_eval_mode)

    if any(r.get("eval_mode") == "circular_base" for r in records):
        total_pos = sum(r.get("n_positions", 0) for r in records)
        correct_pos = sum(r.get("n_correct_positions", 0) for r in records)
        summary["position_level_accuracy"] = (
            correct_pos / total_pos if total_pos else 0
        )
        summary["total_position_calls"] = total_pos

    with open(sum_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # ----- Report -----
    logger.info(f"\n{'='*40}\nEval Done. Total {summary['total']} records.")
    logger.info(f"Overall accuracy: {summary['overall_accuracy']*100:.2f}%")
    logger.info("By eval-mode:")
    for k, v in sorted(summary["by_eval_mode"].items()):
        logger.info(f"  {k:18s}  n={v['n']:4d}  acc={v['accuracy']*100:.2f}%")
    if "position_level_accuracy" in summary:
        logger.info(
            f"\nCircular position-level accuracy: {summary['position_level_accuracy']*100:.2f}% "
            f"({summary['total_position_calls']} total position calls)"
        )
    logger.info("\nBy task:")
    for k, v in sorted(summary["by_task"].items()):
        logger.info(f"  {k:18s}  n={v['n']:4d}  acc={v['accuracy']*100:.2f}%")
    logger.info(f"\nSaved to: {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate generated QA against a target MLLM. "
                    "Defaults come from eval_config.json; CLI args override."
    )
    parser.add_argument("--config", default=DEFAULT_PIPELINE_CONFIG,
                        help="Pipeline config (PROVIDERS section).")
    parser.add_argument("--eval-config", default=DEFAULT_EVAL_CONFIG,
                        help="Eval config (EVAL_MODES + defaults).")

    parser.add_argument("--data-root", default=None, help="override DATA.data_root")
    parser.add_argument("--out-dir",   default=None, help="override DATA.out_dir")
    parser.add_argument("--model",     default=None, help="override TARGET.model")
    parser.add_argument("--model-alias", default=None, help="override TARGET.model_alias")
    parser.add_argument("--judge-provider", default=None, help="override TARGET.judge_provider")
    parser.add_argument("--task",    default=None, help="Filter to a single task.")
    parser.add_argument("--qa-type", default=None, help="Filter to a single qa_type.")
    parser.add_argument("--limit",   type=int, default=0, help="Total row cap (0 = no limit).")
    parser.add_argument("--per-task-limit", type=int, default=0,
                        help="Cap unique samples per task (0 = no limit).")
    parser.add_argument("--tag",     default="", help="Output dir suffix.")
    parser.add_argument(
        "--modes", default=None,
        help="Comma-separated eval-mode keys from EVAL_MODES (e.g. '1' or '2,5'). "
             "Falls back to RUN.selected_modes.",
    )
    args = parser.parse_args()
    run_eval(args)
