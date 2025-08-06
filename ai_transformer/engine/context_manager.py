import uuid
import os
import json
from .utils import logger


class ContextManager:
    def __init__(self, context_file=None):
        self.context_file = context_file
        self.context_data = {}

        if context_file and os.path.exists(context_file):
            try:
                with open(context_file, 'r') as f:
                    self.context_data = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load existing context file: {e}")

    def generate_context_id(self, file_path: str) -> str:
        context_id = str(uuid.uuid4())
        self.context_data[file_path] = context_id
        return context_id

    def get_context_id(self, file_path: str) -> str:
        return self.context_data.get(file_path, None)

    def save(self):
        if self.context_file:
            try:
                with open(self.context_file, 'w') as f:
                    json.dump(self.context_data, f, indent=2)
                logger.info(f"[CONTEXT] Context map saved to {self.context_file}")
            except Exception as e:
                logger.warning(f"[CONTEXT] Failed to save context: {e}")
