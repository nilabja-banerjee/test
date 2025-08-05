class BaseAIProvider:
    def __init__(self, config):
        self.config = config

    def generate_response(self, prompt, context):
        raise NotImplementedError("Subclasses must implement this method")
