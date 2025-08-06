import os
import re
import time
import yaml
import json
from jinja2 import Template

from .logger import get_logger
from .model_router import ModelRouter  # Now used for all model calls

logger = get_logger()


def load_config(config_path='config.yml'):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_prompt(prompt_path):
    """
    Load structured YAML prompt with 'system' and 'user' roles.
    """
    with open(prompt_path, 'r') as f:
        return yaml.safe_load(f)


def render_prompt(prompt_dict, context_dict):
    """
    Render just the user part for logging/debugging.
    """
    template = Template(prompt_dict.get("user", ""))
    return template.render(**context_dict)


def build_chat_messages(prompt_dict, context_dict):
    """
    Render system + user messages for structured chat input.
    """
    messages = []
    if "system" in prompt_dict:
        system_msg = Template(prompt_dict["system"]).render(**context_dict)
        messages.append({"role": "system", "content": system_msg})
    if "user" in prompt_dict:
        user_msg = Template(prompt_dict["user"]).render(**context_dict)
        messages.append({"role": "user", "content": user_msg})
    return messages


def call_model(task_name, messages, config):
    """
    Use ModelRouter to route model calls based on task name.
    """
    router = ModelRouter(config)
    return router.route(task_name, messages)


def clean_generated_code(ai_output):
    """
    Remove markdown formatting and extract raw Java code.
    """
    code_blocks = re.findall(r'```java\n(.*?)```', ai_output, re.DOTALL)
    return code_blocks[0].strip() if code_blocks else ai_output.strip()


def save_output_file(content, class_name, output_dir, suffix="", relative_path=""):
    if not content.strip():
        return

    # Maintain folder hierarchy
    target_path = os.path.join(output_dir, os.path.dirname(relative_path))
    os.makedirs(target_path, exist_ok=True)

    filename = f"{class_name}{suffix}.java"
    filepath = os.path.join(target_path, filename)

    with open(filepath, "w") as f:
        f.write(content)



def load_all_contexts(config):
    """
    Load scanner metadata + file content for transformer input.
    """
    context_dir = config['output_dir']
    file_path = os.path.join(context_dir, "file_metadata.json")

    with open(file_path, 'r') as f:
        file_metadata = json.load(f)

    contexts = {}
    for meta in file_metadata:
        try:
            if 'absolute_path' not in meta or 'relative_path' not in meta:
                logger.error(f"[{meta.get('filename', 'UNKNOWN')}] Missing path info: {meta}")
                continue

            with open(meta['absolute_path'], 'r') as f:
                content = f.read()

            class_name = os.path.splitext(meta['filename'])[0]
            contexts[class_name] = {
                "class_name": class_name,
                "relative_path": meta['relative_path'],
                "file_content": content
            }

        except Exception as e:
            logger.error(f"[{meta.get('filename', 'UNKNOWN')}] Failed to process: {e}")

    return contexts
