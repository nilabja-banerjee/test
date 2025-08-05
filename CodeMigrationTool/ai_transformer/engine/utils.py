import os
import yaml
import time
import re
import json
from jinja2 import Template
from .logger import get_logger
from langchain.chat_models import ChatOllama
from langchain.schema import HumanMessage

logger = get_logger()


def load_yaml_config(path):
    """Load YAML configuration from file."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def load_prompt(prompt_path):
    """Read raw prompt content from file."""
    with open(prompt_path, 'r') as f:
        return f.read()


def render_prompt(prompt_template, context_dict):
    """Render a Jinja2 template with given context."""
    template = Template(prompt_template)
    return template.render(**context_dict)


def call_model(prompt, model_config, llm_settings):
    """Call the AI model (via LangChain or custom REST provider)."""
    provider = model_config['provider']
    model_name = model_config['model_name']
    logger.info(f"Calling model [{provider}::{model_name}]")

    if provider == "langchain":
        llm = ChatOllama(
            model=model_name,
            temperature=llm_settings['temperature'],
            timeout=llm_settings['model_timeout']
        )
        start = time.time()
        response = llm([HumanMessage(content=prompt)]).content
        duration = time.time() - start
        logger.info(f"Model responded in {round(duration, 2)} seconds")
        return response

    elif provider == "custom":
        raise NotImplementedError("Custom provider API not implemented yet")

    else:
        raise ValueError(f"Unsupported provider: {provider}")


def clean_generated_code(ai_output):
    """
    Remove markdown formatting, explanations, and extract raw Java code block.
    """
    code_blocks = re.findall(r'```java\n(.*?)```', ai_output, re.DOTALL)
    if code_blocks:
        return code_blocks[0]
    return ai_output.strip()


def save_output_file(content, class_name, output_dir, suffix=""):
    """Save Java file with optional version suffix."""
    filename = f"{class_name}{suffix}.java"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w') as f:
        f.write(content)
    logger.info(f"Saved file: {filepath}")


def load_config(config_path='config.yml'):
    """Wrapper to load config via YAML."""
    return load_yaml_config(config_path)


def load_all_contexts(config):
    """
    Load the class-level context files (from scanner output) into a dict.
    Reads absolute path instead of reconstructing from relative_path.
    """
    context_dir = config['output_dir']
    file_path = os.path.join(context_dir, "file_metadata.json")

    with open(file_path, 'r') as f:
        file_metadata = json.load(f)

    contexts = {}
    for meta in file_metadata:
        try:
            # Ensure required keys exist
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
