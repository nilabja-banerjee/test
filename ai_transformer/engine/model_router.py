import time
from ai_transformer.engine.logger import get_logger
from ai_transformer.provider.ollama_provider import OllamaProvider
from ai_transformer.provider.custom_provider import CustomHTTPProvider

logger = get_logger()


class ModelRouter:
    def __init__(self, config: dict):
        """
        Initialize with full config so we can read routing rules.
        """
        self.config = config
        self.model_routing = config.get('model_routing', {})

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

    def route(self, task_name: str, messages: list, context_id: str = "-") -> str:
        """
        Route request to appropriate model based on routing config.
        """
        if task_name not in self.model_routing:
            raise ValueError(f"Missing routing config for task: {task_name}")

        model_config = self.model_routing[task_name]
        provider = model_config['provider']
        model_name = model_config['model_name']

        logger.info(f"[{context_id}] Calling model [{provider}::{model_name}] for task: {task_name}")
        model = self.get_model_instance(provider, model_name)

        start = time.time()
        try:
            result = model.chat(messages, context_id=context_id)
        except Exception as e:
            raise RuntimeError(f"[{context_id}] Model call failed: {str(e)}")

        duration = time.time() - start
        logger.info(f"[{context_id}] Model responded in {round(duration, 2)} seconds")
        return result

    def check_model_health(self):
        """
        Check if each model in the routing map is responding.
        Raises an error if any model is unreachable or returns an invalid response.
        """
        for task, model_config in self.config.get("model_routing", {}).items():
            provider = model_config.get("provider")
            model_name = model_config.get("model_name")

            try:
                # Use a more meaningful prompt, especially for instruction-tuned models
                messages = [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say hello if you're active."}
                ]
                start = time.time()
                result = self.route(task, messages, context_id=f"HEALTHCHECK_{task}")
                duration = round(time.time() - start, 2)

                if not result or result.strip() == "":
                    raise ValueError("Empty response from model")

                logger.info(f"[HEALTHCHECK_{task}] ✅ Model responded in {duration}s: {result[:80]}")

            except Exception as e:
                raise RuntimeError(
                    f"[Startup Failure] Model health check failed for task '{task}' → [{provider}::{model_name}]: {str(e)}"
                )
