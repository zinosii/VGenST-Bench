import ast
import json
import logging
import re

from json_repair import repair_json

from llm_client import LLMClient


class BaseAgent:
    def __init__(self, logger: logging.Logger, client: LLMClient):
        self.logger = logger
        self.client = client

    def query_llm(self, messages):
        return self.client.chat(messages)

    def fix_json(self, llm_output_text):
        try:
            if not llm_output_text:
                return None

            text = re.sub(r'```json\s*|\s*```', '', llm_output_text, flags=re.MULTILINE).strip()
            text = text.replace('{{', '{').replace('}}', '}')

            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                text = match.group(1)

            # Strategy A: JSON
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass

            # Strategy B: Python literal_eval
            try:
                py_text = text.replace("true", "True").replace("false", "False").replace("null", "None")
                return ast.literal_eval(py_text)
            except (ValueError, SyntaxError, TypeError):
                # Strategy C: json_repair
                try:
                    parsed = repair_json(text, return_objects=True)
                    if isinstance(parsed, (dict, list)):
                        return parsed
                    self.logger.warning(f"Repaired JSON is not a dict/list: {parsed}")
                    return None
                except Exception as e:
                    self.logger.warning(f"Failed to repair JSON: {e}")
                    return None

        except Exception as e:
            self.logger.error(f"Unexpected critical error in fix_json: {e}")
            return None
