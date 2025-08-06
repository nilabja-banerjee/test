import os
from jinja2 import Template

class PromptLoader:
    def __init__(self, prompt_dir):
        self.prompt_dir = prompt_dir

    def load(self, filename, context):
        file_path = os.path.join(self.prompt_dir, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Prompt file not found: {file_path}")
        with open(file_path, 'r') as f:
            raw_prompt = f.read()
        template = Template(raw_prompt)
        return template.render(context)
