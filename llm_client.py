import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Optional

from anthropic import Anthropic
from openai import OpenAI

try:
    from google import genai as google_genai
    _HAS_GEMINI = True
except ImportError:
    _HAS_GEMINI = False


RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SEC = 1.0


class LLMClient(ABC):
    def __init__(self, logger: logging.Logger, model: str, temperature: float, max_tokens: int):
        self.logger = logger
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def _raw_chat(self, messages: list) -> str:
        ...

    def chat(self, messages: list) -> Optional[str]:
        cls_name = self.__class__.__name__
        for attempt in range(1, RETRY_ATTEMPTS + 1):
            try:
                return self._raw_chat(messages)
            except Exception as e:
                if attempt >= RETRY_ATTEMPTS:
                    self.logger.error(
                        f"[{cls_name}] failed after {RETRY_ATTEMPTS} attempts: {e}"
                    )
                    return None
                wait = RETRY_BACKOFF_SEC * (2 ** (attempt - 1))
                self.logger.warning(
                    f"[{cls_name}] attempt {attempt}/{RETRY_ATTEMPTS} failed: {e}. "
                    f"retrying in {wait:.1f}s..."
                )
                time.sleep(wait)
        return None


class ClaudeClient(LLMClient):
    def __init__(self, logger, api_key, model, temperature, max_tokens):
        super().__init__(logger, model, temperature, max_tokens)
        self.client = Anthropic(api_key=api_key)

    # claude api

    def _raw_chat(self, messages):
        system_prompt = ""
        conv = []
        for m in messages:
            if m["role"] == "system":
                system_prompt = m["content"]
            else:
                conv.append({"role": m["role"], "content": m["content"]})

        system_param = None
        if system_prompt:
            system_param = [{
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }]

        resp = self.client.messages.create(
            model=self.model,
            system=system_param,
            messages=conv,
            thinking={"type": "adaptive"},
            output_config={"effort": "low"},
            max_tokens=self.max_tokens,
        )
        return resp.content[0].text


class OpenAIClient(LLMClient):
    def __init__(self, logger, api_key, model, temperature, max_tokens, base_url=None):
        super().__init__(logger, model, temperature, max_tokens)
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)
        self.base_url = base_url

    def _raw_chat(self, messages):
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return resp.choices[0].message.content


class GeminiClient(LLMClient):
    def __init__(self, logger, api_key, model, temperature, max_tokens):
        if not _HAS_GEMINI:
            raise RuntimeError(
                "google-genai is not installed. Run: pip install google-genai"
            )
        super().__init__(logger, model, temperature, max_tokens)
        self.client = google_genai.Client(api_key=api_key)

    def _raw_chat(self, messages):
        system_prompt = ""
        contents = []
        for m in messages:
            role = m["role"]
            content = m["content"]
            if role == "system":
                system_prompt = content if isinstance(content, str) else str(content)
            else:
                gemini_role = "model" if role == "assistant" else "user"
                contents.append({"role": gemini_role, "parts": [{"text": str(content)}]})

        config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_tokens,
        }
        if system_prompt:
            config["system_instruction"] = system_prompt

        resp = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )
        return resp.text


class LLMClientFactory:
    def __init__(self, providers_config: dict, logger: logging.Logger):
        self.providers_config = providers_config
        self.logger = logger

    def build(self, worker_cfg: dict) -> LLMClient:
        provider_name = worker_cfg["provider"]
        if provider_name not in self.providers_config:
            raise ValueError(
                f"Unknown provider {provider_name!r}. "
                f"Available: {list(self.providers_config.keys())}"
            )

        pcfg = self.providers_config[provider_name]
        ptype = pcfg["type"]

        model = self._resolve_model(pcfg, worker_cfg.get("model", "default"))
        api_key = self._resolve_api_key(pcfg)
        temperature = worker_cfg["temperature"]
        max_tokens = worker_cfg["max_tokens"]

        if ptype == "anthropic":
            return ClaudeClient(
                self.logger, api_key, model, temperature, max_tokens
            )
        if ptype in ("openai", "openai_compatible"):
            base_url = pcfg.get("base_url") if ptype == "openai_compatible" else None
            if ptype == "openai_compatible" and not base_url:
                raise ValueError(
                    f"provider {provider_name!r} (type=openai_compatible) requires 'base_url'"
                )
            return OpenAIClient(
                self.logger, api_key, model, temperature, max_tokens,
                base_url=base_url,
            )
        if ptype == "gemini":
            return GeminiClient(
                self.logger, api_key, model, temperature, max_tokens
            )
        raise ValueError(
            f"Unsupported provider type {ptype!r} for {provider_name!r}. "
            f"Expected one of: anthropic, openai, openai_compatible, gemini"
        )

    @staticmethod
    def _resolve_model(provider_cfg: dict, alias: str) -> str:
        models = provider_cfg.get("models", {})
        return models.get(alias, alias)

    @staticmethod
    def _resolve_api_key(provider_cfg: dict) -> str:
        api_key = provider_cfg.get("api_key")
        if api_key:
            return api_key

        env_name = provider_cfg.get("api_key_env")
        if env_name:
            val = os.environ.get(env_name)
            if not val:
                raise RuntimeError(
                    f"Environment variable {env_name!r} is not set. "
                    f"Export it or use 'api_key' in config."
                )
            return val

        raise RuntimeError(
            "Provider config must specify either 'api_key' or 'api_key_env'."
        )
