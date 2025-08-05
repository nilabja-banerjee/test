import os
import yaml
from jinja2 import Template
from langchain_community.llms import Ollama
from ..engine.logger import get_logger

logger = get_logger()

def load_config():
    with open("config.yml", "r") as f:
        return yaml.safe_load(f)

def load_feedback_prompt(prompt_path):
    with open(prompt_path, "r", encoding="utf-8") as f:
        return Template(f.read())

def call_reviewer_llm(prompt_text, model_name, temperature=0.2, timeout=60):
    llm = Ollama(model=model_name, temperature=temperature, timeout=timeout)
    logger.info(f"[{model_name}] Running feedback check...")
    return llm.invoke(prompt_text)

def run_reviewer_on_pair(source_path, generated_path, rel_path):
    config = load_config()
    prompt_template_path = os.path.join(config["prompt_dir"], "source_vs_generated_feedback.txt")
    reviewer_model = config["reviewer_model"]["model_name"]

    if not os.path.exists(source_path) or not os.path.exists(generated_path):
        logger.warning(f"[SKIP] Missing file pair: {rel_path}")
        return None

    with open(source_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    with open(generated_path, "r", encoding="utf-8") as f:
        generated_code = f.read()

    prompt_template = load_feedback_prompt(prompt_template_path)
    filled_prompt = prompt_template.render(
        source_code=source_code,
        generated_code=generated_code
    )

    response = call_reviewer_llm(filled_prompt, reviewer_model)

    feedback_path = generated_path + ".review_feedback.txt"
    with open(feedback_path, "w", encoding="utf-8") as f:
        f.write(response)

    logger.info(f"📝 Feedback written: {feedback_path}")
    return feedback_path
