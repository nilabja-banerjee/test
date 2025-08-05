from langchain.llms import Ollama
from .base import BaseAIProvider

class LangChainProvider(BaseAIProvider):
    def __init__(self, config):
        super().__init__(config)
        self.model = Ollama(model=config["model_name"], temperature=config.get("temperature", 0.3))

    def generate_response(self, prompt, context):
        full_prompt = prompt.format(**context)
        return self.model(full_prompt)
