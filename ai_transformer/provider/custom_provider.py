import time
import requests
from langchain.schema import HumanMessage, SystemMessage
from ai_transformer.engine.logger import get_logger
from .config_loader import load_config

class CustomHTTPProvider:
    def __init__(self, model_name):
        """
        Initialize Custom Provider using config.yml settings.
        """
        self.logger = get_logger()
        self.model_name = model_name
        self.config = load_config()

        # Load custom provider section
        provider_cfg = self.config.get("custom_provider", {})
        self.api_url = provider_cfg.get("base_url", "").rstrip("/") + provider_cfg.get("endpoint", "/chat/completions")

        # Optional headers (including auth if provided)
        self.headers = provider_cfg.get("headers", {
            "Content-Type": "application/json"
        })

        # Load shared model settings
        self.settings = self.config.get("llm_settings", {
            "temperature": 0.2,
            "max_tokens": 2048,
            "model_timeout": 120
        })

    def _convert_messages_to_openai_format(self, messages):
        """
        Convert LangChain-style messages to OpenAI-compatible JSON format.
        """
        converted = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                role = "system"
            elif isinstance(msg, HumanMessage):
                role = "user"
            else:
                raise ValueError(f"Unsupported message type: {type(msg)}")
            converted.append({"role": role, "content": msg.content})
        return converted

    def chat(self, messages, context_id="-"):
        """
        Send request to the remote model with OpenAI-style chat format.
        """
        payload = {
            "messages": self._convert_messages_to_openai_format(messages),
            "temperature": self.settings.get("temperature", 0.3),
            "max_tokens": self.settings.get("max_tokens", 2048),
            "stream": False
        }

        try:
            start = time.time()
            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=self.settings.get("model_timeout", 90)
            )
            duration = round(time.time() - start, 2)
            self.logger.info(f"[{context_id}] Custom model responded in {duration} seconds")

            if response.status_code == 200:
                res_json = response.json()
                return res_json.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            else:
                self.logger.error(f"[{context_id}] HTTP {response.status_code}: {response.text}")
                return f"Model HTTP Error: {response.status_code}"

        except Exception as e:
            self.logger.error(f"[{context_id}] Custom model call failed: {e}")
            return "Custom model call failed."
