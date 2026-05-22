<h1 align="center">
  VGenST-Bench: A Benchmark for Spatio-Temporal Reasoning via Active Video Synthesis
</h1>

<p align="center">
  <b>Jinho Park<sup>1</sup> · Youbin Kim<sup>1</sup> · Hogun Park<sup>1</sup> · Eunbyung Park<sup>2†</sup></b><br>
  <sup>1</sup>Sungkyunkwan University &nbsp;·&nbsp; <sup>2</sup>Yonsei University<br>
  <sup>†</sup>Corresponding author
</p>

<p align="center">
  <a href="https://arxiv.org/abs/2605.22570" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/Paper-VGenST--Bench-B31B1B?style=for-the-badge&logo=arxiv&logoColor=white&labelColor=2C2C2C" alt="Paper"></a>
  <a href="https://zinosii.github.io/VGenST-Bench/" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/Webpage-VGenST--Bench-2196F3?style=for-the-badge&logo=googlechrome&logoColor=white&labelColor=2C2C2C" alt="Webpage"></a>
  <a href="https://huggingface.co/datasets/zino1/VGenST-Bench" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/Dataset-VGenST--Bench-FFD21E?style=for-the-badge&logo=huggingface&logoColor=white&labelColor=2C2C2C" alt="Dataset"></a>
</p>

---

## Introduction

**VGenST-Bench** is a fully **generative** benchmark for evaluating **spatio-temporal reasoning** in Multimodal Large Language Models (MLLMs). Every video, scene graph, scenario, prompt, and QA pair is produced by a controllable agent pipeline, giving precise control over scene composition, camera trajectory, and reasoning targets.

The benchmark covers:

- **12 reasoning tasks** organized over three spatial scales — Figural, Vista, Environmental
- **12 QA types** across three reasoning levels — Visual Perception (L1), Scene Understanding (L2), Spatio-Temporal Reasoning (L3)
- **4 question variants** per QA — Base MCQ, NoT-Distractor, NoT-Answer, Open-Ended — to probe positional bias and false / true abstention
- **1,200 videos** (12 tasks × 100 themes), each paired with the full generation provenance

## Pipeline

The pipeline jointly synthesizes scene graphs, scenarios, videos, and QA sets through four agents, each backed by an LLM provider (Claude / OpenAI / Gemini / vLLM-served local models) and, where applicable, image/video generative models:

| Stage | Agent | Output |
|---|---|---|
| 1 | **SceneGraphAgent** | Task-grounded scene graph from a theme |
| 2 | **ScenarioAgent**   | Temporal scenario over the scene graph |
| 3 | **VideoAgent**      | Image prompt → first frame → video prompt → video |
| 4 | **QAAgent**         | Multiple-choice QA across applicable QA types |

## Installation

```bash
git clone https://github.com/NeurIPS2026-VGenST-Bench/VGenST-Bench.git
cd VGenST-Bench
pip install -r requirements.txt
```

Set provider API keys as environment variables (only the providers you intend to use are required):

```bash
export ANTHROPIC_API_KEY=...
export OPENAI_API_KEY=...
export GOOGLE_API_KEY=...
export ATLASCLOUD_API_KEY=...
```

## Configuration

Pipeline behavior is controlled by [config.json](config.json):

- **`OVERALL.mode`** — `benchmark` (iterates over `TARGET_TASKS` × `THEMES_<TASK>` from [utils/settings.py](utils/settings.py)) or `custom` (uses themes from `OVERALL.custom_themes` or `--themes` CLI flag)
- **`OVERALL.running_agents`** — toggle each stage on/off; set `RESUME_FROM` to a previous run timestamp (e.g. `20260507_120000`) to load earlier-stage outputs from `outputs/<RESUME_FROM>/`
- **`PROVIDERS`** — register LLM providers (anthropic / openai / openai_compatible / gemini / atlascloud) with API keys and model aliases
- **`SCENE_GRAPH_AGENT` / `SCENARIO_AGENT` / `VIDEO_AGENT` / `QA_AGENT`** — per-worker provider, model, temperature, max_tokens
- **`IMAGE_MODELS` / `VIDEO_MODELS`** — per-model generation parameters for AtlasCloud-hosted media models

## Usage

### Benchmark mode

```bash
python VGenST_run.py --config config.json
```

Iterates every task in `TARGET_TASKS` and every theme in `THEMES_<TASK>`. Outputs land under `outputs/<timestamp>/`.

### Custom mode (specific themes)

```bash
python VGenST_run.py --themes "a busy hospital corridor" "an empty parking lot at night"
```

The agent's task selector routes each theme to the most appropriate task automatically.

### Resuming a run

To rerun only the QA stage on a previous run's scene graphs and scenarios, set in `config.json`:

```json
"running_agents": {
    "SCENE_GRAPH_AGENT": "False",
    "SCENARIO_AGENT":    "False",
    "VIDEO_AGENT":       "False",
    "QA_AGENT":          "True",
    "RESUME_FROM":       "20260507_120000"
}
```

### Evaluation

```bash
python eval.py --config eval_config.json
```

Configure target / judge models, eval modes (vanilla, circular, reformulation variants v1–v3), task / qa_type filters, and frame sampling in [eval_config.json](eval_config.json).

## Repository Layout

```
VGenST-final/
├── VGenST_run.py              # Pipeline orchestrator
├── eval.py                    # Evaluation harness
├── config.json                # Pipeline config
├── eval_config.json           # Evaluation config
├── llm_client.py              # Unified LLM client (Claude / OpenAI / Gemini / vLLM)
├── media_client.py            # Image / video generation client (AtlasCloud)
├── agents/
│   ├── base_agent.py
│   ├── scene_graph_agent.py
│   ├── scenario_agent.py
│   ├── video_agent.py
│   └── qa_agent.py
├── sysprompt/                 # Per-agent system prompts and templates
│   ├── scene_graph_agent/
│   ├── scenario_agent/
│   ├── video_agent/
│   └── qa_agent/
│       └── tasks/<TASK>/distractor_pool.json
└── utils/
    └── settings.py            # TARGET_TASKS, THEMES_<TASK>
```

## Tasks (3 × 2 × 2 Taxonomy)

| Scale × Dynamics | Egocentric | Exocentric |
|---|---|---|
| **Figural** Static  | MC: Multi-Container Attribute Mapping | CI: Container Intersection Inference |
| **Figural** Dynamic | QC: Quantity Change Tracking          | CM: Causal Mapping |
| **Vista** Static    | DE: Direction Estimation              | HO: Height Ordering |
| **Vista** Dynamic   | IO: Interacted Object Identification  | VI: Visibility Identification |
| **Environmental** Static  | DS: Directional Signage Grounding | LS: Landmark Spatial Composition |
| **Environmental** Dynamic | RV: Relative Velocity Identification | BT: Behavioral Trigger Identification |

## QA Types (3-Level Hierarchy)

| L1: Visual Perception | L2: Scene Understanding | L3: Spatio-Temporal Reasoning |
|---|---|---|
| Object Existence (OE)            | Identity Tracking (IT)        | Perspective-Taking (PT)    |
| Object Attribute Recognition (OA)| Action Recognition (AR)       | Counterfactual Reasoning (CR) |
| 2D Frame Localization (FL)       | Object Counting (OC)          | Predictive Reasoning (PR)  |
|                                  | Temporal Ordering (TO)        |                            |
|                                  | Camera Motion Recognition (CM)|                            |
|                                  | Spatial Layout Understanding (SL) |                       |

A task–QA applicability matrix ([sysprompt/qa_agent/applicability_matrix.py](sysprompt/qa_agent/applicability_matrix.py)) specifies which QA types are evaluated for each of the 12 tasks.

## Citation

```bibtex
@misc{park2026vgenstbenchbenchmarkspatiotemporalreasoning,
  title         = {VGenST-Bench: A Benchmark for Spatio-Temporal Reasoning via Active Video Synthesis},
  author        = {Jinho Park and Youbin Kim and Hogun Park and Eunbyung Park},
  year          = {2026},
  eprint        = {2605.22570},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CV},
  url           = {https://arxiv.org/abs/2605.22570},
}
```