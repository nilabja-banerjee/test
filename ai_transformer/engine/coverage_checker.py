import os
import re
import json

from .utils import (
    logger,
    call_model,
    render_prompt,
    load_prompt,
    build_chat_messages
)

def check_coverage(source_code, generated_code, config, prompt_dir, context_id):
    """
    Use the reviewer model (via router) to detect gaps between the original and generated code.

    Expected model response format:
    - Coverage: 87%
    - Issues:
      - Missing validation
      - Missing exception handling
    """
    prompt_template = load_prompt(os.path.join(prompt_dir, "review_coverage.yaml"))
    prompt_vars = {
        "source_code": source_code,
        "generated_code": generated_code,
        "context_id": context_id
    }

    logger.info(f"[{context_id}] Sending source and generated code to reviewer model.")
    messages = build_chat_messages(prompt_template, prompt_vars)

    suggestions = call_model("check_coverage", messages, config)
    logger.debug(f"[{context_id}] Raw model response:\n{suggestions}")

    # Parse coverage %
    coverage_match = re.search(r"Coverage\s*[:\-]?\s*(\d+)%", suggestions)
    coverage = int(coverage_match.group(1)) if coverage_match else 0
    if not coverage_match:
        logger.warning(f"[{context_id}] Coverage not found. Defaulting to 0%.")

    # Parse issues from model response
    issues = []
    issue_section = suggestions.split("Issues:")[-1] if "Issues:" in suggestions else ""
    if not issue_section.strip():
        logger.warning(f"[{context_id}] No Issues section found in response.")

    for line in issue_section.strip().splitlines():
        line = line.strip()
        if line.startswith("-") or line.startswith("•"):
            issues.append(line.lstrip("-•").strip())

    logger.info(f"[{context_id}] Parsed Coverage: {coverage}% with {len(issues)} issues.")
    return coverage, issues


def apply_feedback(source_code, generated_code, suggestions, config, prompt_dir, context_id):
    """
    Use the primary model (via router) to improve the generated code using review suggestions.
    """
    prompt_template = load_prompt(os.path.join(prompt_dir, "apply_feedback.yaml"))
    prompt_vars = {
        "source_code": source_code,
        "initial_generated_code": generated_code,
        "review_feedback": suggestions,
        "context_id": context_id
    }

    messages = build_chat_messages(prompt_template, prompt_vars)
    logger.info(f"[{context_id}] Applying feedback via primary model.")

    improved_code = call_model("apply_feedback", messages, config)
    return improved_code
