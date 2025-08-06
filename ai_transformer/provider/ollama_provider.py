from langchain.chat_models import ChatOllama
from langchain.schema import HumanMessage, SystemMessage
import time


class OllamaProvider:
    def __init__(self, model_name, settings=None, logger=None):
        self.model_name = model_name
        self.settings = settings or {
            "temperature": 0.2,
            "model_timeout": 120
        }
        self.logger = logger

    def chat(self, messages, context_id="-"):
        """
        Call Ollama via LangChain with structured system + user messages.

        Args:
            messages (list): List of LangChain-compatible messages
            context_id (str): Optional class name or context for log clarity

        Returns:
            str: Model response content
        """
        try:
            llm = ChatOllama(
                model=self.model_name,
                temperature=self.settings.get('temperature', 0.2),
                timeout=self.settings.get('model_timeout', 120)
            )
            start = time.time()
            response = llm(messages)
            duration = round(time.time() - start, 2)

            if self.logger:
                self.logger.info(f"Model responded in {duration} seconds", context=context_id)

            return response.content

        except Exception as e:
            if self.logger:
                self.logger.error(f"Ollama call failed: {e}", context=context_id)
            return "Ollama model call failed."
