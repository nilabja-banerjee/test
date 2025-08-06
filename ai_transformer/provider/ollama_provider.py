from langchain_community.llms import Ollama
import time
from ai_transformer.engine.logger import get_logger
from .config_loader import load_config

class OllamaProvider:
    def __init__(self, model_name):
        self.model_name = model_name
        self.logger = get_logger()
        self.config = load_config()
        self.settings = self.config.get("llm_settings", {})

    def chat(self, messages, context_id="-"):
        """
        Sends a non-streaming request to the Ollama model using LangChain.
        Converts role-based messages into a single prompt string.
        """
        try:
            # Convert list of messages to string prompt (user + system merged)
            prompt = "\n".join([msg["content"] for msg in messages])

            llm = Ollama(
                model=self.model_name,
                temperature=self.settings.get("temperature", 0.2)
            )

            start = time.time()
            response = llm.invoke(prompt)  # ✅ Correct usage
            duration = round(time.time() - start, 2)
            self.logger.info(f"[{context_id}] Ollama responded in {duration} seconds")

            return response.strip() if isinstance(response, str) else str(response)

        except Exception as e:
            self.logger.error(f"[{context_id}] Ollama model call failed: {e}")
            return "Model call failed"
