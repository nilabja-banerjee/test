import os
import json
from .utils import logger, call_model, render_prompt, load_prompt


def check_coverage(source_code, generated_code, reviewer_model, llm_settings, prompt_dir, context_id):
    """
    Use the reviewer model to detect gaps between the original and generated code.
    """
    prompt_template = load_prompt(os.path.join(prompt_dir, "check_coverage.txt"))
    context = {
        "source_code": source_code,
        "generated_code": generated_code,
        "context_id": context_id
    }
    prompt = render_prompt(prompt_template, context)

    logger.info(f"[{context_id}] Sending source and generated code to reviewer model.")
    suggestions = call_model(prompt, reviewer_model, llm_settings)
    return suggestions


def apply_feedback(source_code, generated_code, suggestions, primary_model, llm_settings, prompt_dir, context_id):
    """
    Use the primary model to improve code using reviewer suggestions.
    """
    prompt_template = load_prompt(os.path.join(prompt_dir, "apply_feedback.txt"))
    context = {
        "source_code": source_code,
        "initial_generated_code": generated_code,
        "review_feedback": suggestions,
        "context_id": context_id
    }
    prompt = render_prompt(prompt_template, context)

    logger.info(f"[{context_id}] Applying feedback via primary model.")
    improved_code = call_model(prompt, primary_model, llm_settings)
    return improved_code
