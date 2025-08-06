import time
from ai_transformer.engine.logger import get_logger
from ai_transformer.provider.ollama_provider import OllamaProvider
from ai_transformer.provider.custom_provider import CustomHTTPProvider

logger = get_logger()


class ModelRouter:
    def __init__(self, config: dict):
        """
        Initialize with full config so we can read routing rules later if needed.
        """
        self.config = config

    def get_model_instance(self, provider: str, model_name: str):
        """
        Returns an instantiated model provider class based on config.
        """
        if provider == "ollama":
            return OllamaProvider(model_name)
        elif provider == "custom":
            return CustomHTTPProvider(model_name)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def route(self, task_name: str, messages: list) -> str:
        """
        Main router method: given a task, use the config to find model/provider and return output.
        """
        if task_name not in self.config['model_routing']:
            raise ValueError(f"Missing routing config for task: {task_name}")

        model_config = self.config['model_routing'][task_name]
        provider = model_config['provider']
        model_name = model_config['model_name']

        logger.info(f"Calling model [{provider}::{model_name}] for task: {task_name}")
        model = self.get_model_instance(provider, model_name)

        start = time.time()
        result = model.chat(messages)
        duration = time.time() - start

        logger.info(f"[{task_name}] Model responded in {round(duration, 2)} seconds")
        return result
