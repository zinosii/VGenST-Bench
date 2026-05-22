import base64
import logging
import os
import time
from typing import Optional

import requests

from llm_client import LLMClientFactory


POLL_INTERVAL_SEC = 20
POLL_MAX_ATTEMPTS = 60
VIDEO_INITIAL_DELAY_SEC = 60


# ==========================================
# Media Client
# ==========================================
class MediaClient:
    def __init__(
        self,
        logger: logging.Logger,
        api_key: str,
        base_url: str,
        image_models_info: dict,
        video_models_info: dict,
    ):
        self.logger = logger
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.image_models_info = image_models_info
        self.video_models_info = video_models_info
        self._headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

    def generate_image(
        self, image_prompt, image_model: str, save_path: str,
        poll_interval: int = POLL_INTERVAL_SEC,
        poll_max_attempts: int = POLL_MAX_ATTEMPTS,
    ) -> Optional[str]:
        try:
            data = self._build_image_data(image_prompt, image_model)
        except Exception as e:
            self.logger.error(f"[MediaClient] build image data failed: {e}")
            return None

        return self._run_job(
            kind="image", data=data, save_path=save_path, model_name=image_model,
            initial_delay=0, poll_interval=poll_interval, poll_max_attempts=poll_max_attempts,
        )

    def generate_video(
        self, video_prompt, first_frame_path: str, video_model: str, save_path: str,
        initial_delay: int = VIDEO_INITIAL_DELAY_SEC,
        poll_interval: int = POLL_INTERVAL_SEC,
        poll_max_attempts: int = POLL_MAX_ATTEMPTS,
    ) -> Optional[str]:
        try:
            data = self._build_video_data(video_prompt, first_frame_path, video_model)
        except Exception as e:
            self.logger.error(f"[MediaClient] build video data failed: {e}")
            return None

        return self._run_job(
            kind="video", data=data, save_path=save_path, model_name=video_model,
            initial_delay=initial_delay, poll_interval=poll_interval,
            poll_max_attempts=poll_max_attempts,
        )

    def _run_job(
        self, kind: str, data: dict, save_path: str, model_name: str,
        initial_delay: int, poll_interval: int, poll_max_attempts: int,
    ) -> Optional[str]:
        endpoint = "generateImage" if kind == "image" else "generateVideo"
        url = f"{self.base_url}/model/{endpoint}"

        try:
            resp = requests.post(url, headers=self._headers, json=data)
            prediction_id = resp.json()["data"]["id"]
            self.logger.info(f"[MediaClient] {kind} job created: id={prediction_id} model={model_name}")
        except Exception as e:
            self.logger.error(f"[MediaClient] POST {endpoint} failed: {e}")
            return None

        if initial_delay:
            time.sleep(initial_delay)

        result_url = self._poll(prediction_id, kind, poll_interval, poll_max_attempts)
        if not result_url:
            return None

        return self._download(result_url, save_path)

    def _poll(self, prediction_id: str, kind: str, interval: int, max_attempts: int) -> Optional[str]:
        poll_url = f"{self.base_url}/model/prediction/{prediction_id}"
        self.logger.info(f"[MediaClient] polling {kind} job (id={prediction_id})")

        for attempt in range(max_attempts):
            try:
                resp = requests.get(poll_url, headers=self._headers)
                result = resp.json()
                status = result.get("data", {}).get("status")

                if status in ("completed", "succeeded"):
                    return result["data"]["outputs"][0]
                if status in ("failed", "timeout"):
                    err = result.get("data", {}).get("error", "Unknown")
                    self.logger.error(f"[MediaClient] {kind} job failed: {err}")
                    return None
            except Exception as e:
                self.logger.warning(
                    f"[MediaClient] poll error ({attempt+1}/{max_attempts}): {e}"
                )
            time.sleep(interval)

        self.logger.error(
            f"[MediaClient] {kind} job timeout after {max_attempts * interval}s"
        )
        return None

    def _download(self, url: str, save_path: str) -> Optional[str]:
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            resp = requests.get(url, stream=True)
            if resp.status_code != 200:
                self.logger.error(
                    f"[MediaClient] download HTTP {resp.status_code}: {url}"
                )
                return None
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
            self.logger.info(f"[MediaClient] saved: {save_path}")
            return save_path
        except Exception as e:
            self.logger.error(f"[MediaClient] download failed: {e}")
            return None

    # ----- Request body builders (model-specific) -----
    def _build_image_data(self, image_prompt, image_model: str) -> dict:
        if image_model not in self.image_models_info:
            raise ValueError(f"Unknown image_model {image_model!r} (not in IMAGE_MODELS config)")
        info = self.image_models_info[image_model]
        prompt = (
            image_prompt["prompt"] if isinstance(image_prompt, dict)
            else str(image_prompt)
        )

        if image_model == "qwen/qwen-image-2.0/text-to-image":
            return {
                "model": info["model"],
                "seed": -1,
                "size": info["size"],
                "prompt": prompt
            }      

        if image_model == "google/nano-banana-2/text-to-image":
            return {
                "model": info["model"],
                "resolution": info["resolution"],
                "output_format": info["output_format"],
                "enable_sync_mode": False,
                "enable_base64_output": False,
                "aspect_ratio": info["aspect_ratio"],
                "prompt": prompt
            }
        
        if image_model == "alibaba/wan-2.7/text-to-image":
            return {
                "model": info["model"],
                "size": info["size"],
                "n": 1,
                "watermark": False,
                "thinking_mode": True,
                "enable_sequential": False,
                "seed": -1,
                "enable_sync_mode": False,
                "enable_base64_output": False,
                "prompt": prompt
            }
            
        if image_model == "qwen/qwen-image-2.0-pro/text-to-image":
            return {
                "model": info["model"],
                "seed": -1,
                "size": info["size"],
                "prompt": prompt
            }
        
        if image_model == "bytedance/seedream-v5.0-lite":
            return {
                "model": info["model"],
                "size": info["size"],
                "enable_base64_output": False,
                "output_format": info["output_format"],
                "prompt": prompt
            }
        

        raise NotImplementedError(
            f"Request body builder not implemented for image_model={image_model!r}. "
            f"Add a branch to MediaClient._build_image_data."
        )

    def _build_video_data(self, video_prompt, first_frame_path: str, video_model: str) -> dict:
        if video_model not in self.video_models_info:
            raise ValueError(f"Unknown video_model {video_model!r} (not in VIDEO_MODELS config)")
        info = self.video_models_info[video_model]
        try :
            first_frame = self._image_to_base64_uri(first_frame_path)
        except Exception as e:
            first_frame = None
        prompt = str(video_prompt)

        if video_model == "bytedance/seedance-v1.5-pro/image-to-video-fast":   
            return {
                "model": info["model"],
                "prompt": prompt,
                "image": first_frame,
                "resolution": info["resolution"],
                "aspect_ratio": info["aspect_ratio"],
                "duration": info["duration"],
                "generate_audio": False,
                "seed": -1,
                "camera_fixed": True,
            }
        
        if video_model == "bytedance/seedance-2.0-fast/image-to-video":
            return {
                "model": info["model"],
                "prompt": prompt,
                "image": first_frame,
                "resolution": info["resolution"],
                "ratio": info["ratio"],
                "duration": info["duration"],
                "generate_audio": False,
                "watermark": False,
                "return_last_frame": False
            }
            
        if video_model == "vidu/q3-turbo/start-end-to-video":
            return {
                "model": info["model"],
                "duration": info["duration"],
                "bgm": False,
                "generate_audio": False,
                "image": first_frame,
                "movement_amplitude": info["movement_amplitude"],
                "resolution": info["resolution"],
                "prompt": prompt,
            }

        if video_model == "vidu/q3-pro/start-end-to-video":
            return {
                "model": info["model"],
                "duration": info["duration"],
                "bgm": False,
                "generate_audio": False,
                "image": first_frame,
                "movement_amplitude": info["movement_amplitude"],
                "resolution": info["resolution"],
                "prompt": prompt,
            }

        if video_model == "alibaba/wan-2.6/image-to-video-flash":
            return {
                "model": info["model"],
                "seed": -1,
                "image": first_frame,
                "duration": info["duration"],
                "shot_type": "single",
                "resolution": "720p",
                "enable_prompt_expansion": True,
                "prompt": prompt,
                "generate_audio": False,
            }

        if video_model == "alibaba/wan-2.7/image-to-video":
            return {
                "model": info["model"],
                "seed": -1,
                "image": first_frame,
                "duration": info["duration"],
                "resolution": info["resolution"],
                "prompt_extend": True,
                "watermark": False,
                "prompt": prompt,
            }
        
        if video_model == "kwaivgi/kling-v3.0-std/image-to-video":
            return {
                "model": info["model"],
                "cfg_scale": info["cfg_scale"],
                "duration": info["duration"],
                "sound": False,
                "image": first_frame,
                "prompt": prompt,
            }

        if video_model == "kwaivgi/kling-v3.0-pro/image-to-video":
            return {
                "model": info["model"],
                "cfg_scale": info["cfg_scale"],
                "duration": info["duration"],
                "sound": False,
                "image": first_frame,
                "prompt": prompt,
            }

        if video_model == "google/veo3.1-fast/image-to-video":
            return {
                "model": info["model"],
                "resolution": info["resolution"],
                "duration": info["duration"],
                "aspect_ratio": info["aspect_ratio"],
                "prompt": prompt,
                "image": first_frame,
            }

        if video_model == "bytedance/seedance-2.0-fast/text-to-video":
            return {
                "model": info["model"],
                "prompt": prompt,
                "resolution": info["resolution"],
                "ratio": info["ratio"],
                "duration": info["duration"],
                "generate_audio": False,
                "watermark": False,
                "return_last_frame": False
            }

        if video_model == "bytedance/seedance-2.0/text-to-video":
            return {
                "model": info["model"],
                "prompt": prompt,
                "resolution": info["resolution"],
                "ratio": info["ratio"],
                "duration": info["duration"],
                "generate_audio": False,
                "watermark": False,
                "return_last_frame": False
            }

        raise NotImplementedError(
            f"Request body builder not implemented for video_model={video_model!r}. "
            f"Add a branch to MediaClient._build_video_data."
        )

    @staticmethod
    def _image_to_base64_uri(image_path: str) -> str:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        ext = image_path.rsplit(".", 1)[-1].lower()
        mime_type = "image/png" if ext == "png" else "image/jpeg"
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"


# ==========================================
# Factory
# ==========================================
class MediaClientFactory:
    def __init__(
        self,
        providers_config: dict,
        image_models_info: dict,
        video_models_info: dict,
        logger: logging.Logger,
    ):
        self.providers_config = providers_config
        self.image_models_info = image_models_info
        self.video_models_info = video_models_info
        self.logger = logger

    def build(self, worker_cfg: dict) -> MediaClient:
        provider_name = worker_cfg["provider"]
        if provider_name not in self.providers_config:
            raise ValueError(
                f"Unknown provider {provider_name!r}. "
                f"Available: {list(self.providers_config.keys())}"
            )

        pcfg = self.providers_config[provider_name]
        ptype = pcfg.get("type")

        if ptype != "atlascloud":
            raise ValueError(
                f"Unsupported media provider type {ptype!r} for {provider_name!r}. "
                f"Expected: 'atlascloud'."
            )

        base_url = pcfg.get("base_url")
        if not base_url:
            raise ValueError(f"provider {provider_name!r} missing 'base_url'")

        api_key = LLMClientFactory._resolve_api_key(pcfg)

        return MediaClient(
            logger=self.logger,
            api_key=api_key,
            base_url=base_url,
            image_models_info=self.image_models_info,
            video_models_info=self.video_models_info,
        )
