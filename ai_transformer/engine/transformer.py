import os
import json
from .utils import (
    load_prompt,
    render_prompt,
    build_chat_messages,
    clean_generated_code,
    save_output_file,
    load_config,
    load_all_contexts
)
from .coverage_checker import check_coverage, apply_feedback
from .logger import get_logger
from .model_router import ModelRouter

logger = get_logger()

class CodeTransformer:
    def __init__(self, config_path='config.yml'):
        self.config = load_config(config_path)
        self.source_dir = self.config['source_code_base']
        self.output_dir = self.config['output_dir']
        self.prompt_dir = self.config['prompt_dir']
        self.task_map = self.config.get('task_map', {})
        self.llm_settings = self.config.get('llm_settings', {})

        # ✅ Initialize ModelRouter here
        self.model_router = ModelRouter(self.config)

        # ✅ Check model health on startup
        self.model_router.check_model_health()

        os.makedirs(self.output_dir, exist_ok=True)
        self.context_data = load_all_contexts(self.config)

    def call_task_model(self, task_name: str, context_vars: dict, context_id: str) -> str:
        """
        Generic wrapper to build prompt + route to correct model for a given task.
        """
        if task_name not in self.task_map:
            raise ValueError(f"Missing prompt mapping for task: {task_name}")

        prompt_path = os.path.join(self.prompt_dir, self.task_map[task_name])
        prompt = load_prompt(prompt_path)
        messages = build_chat_messages(prompt, context_vars)

        # ✅ Route using unified router with context ID
        return self.model_router.route(task_name, messages, context_id=context_id)

    def transform_file(self, class_name, file_meta, file_content):
        context_id = f"{class_name}"
        logger.info(f"[{context_id}] Transforming file {file_meta.get('relative_path', 'N/A')}")

        # Step 1: Transform
        prompt_vars = {
            "class_name": class_name,
            "file_content": file_content,
            "relative_path": file_meta.get("relative_path", "")
        }
        raw_response = self.call_task_model("transform_class", prompt_vars, context_id)

        # ✅ Skip if model call failed or returned junk
        if not raw_response or "model call failed" in raw_response.lower():
            logger.error(f"[{context_id}] Model call failed. Skipping.")
            return

        transformed_code = clean_generated_code(raw_response)
        save_output_file(transformed_code, class_name, self.output_dir, suffix="_v1")

        # Step 2: Coverage Review
        coverage, issues = check_coverage(
            source_code=file_content,
            generated_code=transformed_code,
            config=self.config,
            prompt_dir=self.prompt_dir,
            context_id=context_id
        )

        # Step 3: Apply Feedback Iteratively
        iteration = 1
        while coverage < 99 and iteration <= 3:
            logger.warning(f"[{context_id}] Coverage {coverage}%. Iteration {iteration}...")

            transformed_code = apply_feedback(
                source_code=file_content,
                generated_code=transformed_code,
                suggestions="\n".join(issues),
                config=self.config,
                prompt_dir=self.prompt_dir,
                context_id=context_id
            )

            save_output_file(transformed_code, class_name, self.output_dir, suffix=f"_v{iteration + 1}")
            coverage, issues = check_coverage(
                source_code=file_content,
                generated_code=transformed_code,
                config=self.config,
                prompt_dir=self.prompt_dir,
                context_id=context_id
            )

            iteration += 1

        logger.info(f"[{context_id}] Final coverage: {coverage}%")
        if coverage < 100:
            logger.warning(f"[{context_id}] Issues remaining:\n{json.dumps(issues, indent=2)}")

        return transformed_code

    def run(self):
        for class_name, context in self.context_data.items():
            try:
                relative_path = context.get("relative_path")
                file_content = context.get("file_content", "")
                if not relative_path or not file_content:
                    logger.warning(f"[{class_name}] Missing data. Skipping.")
                    continue

                abs_path = os.path.join(self.source_dir, relative_path)
                file_meta = {
                    "filename": f"{class_name}.java",
                    "relative_path": relative_path,
                    "absolute_path": abs_path
                }
                self.transform_file(class_name, file_meta, file_content)
            except Exception as e:
                logger.error(f"[{class_name}] Failed to process: {e}")


def run_transformation():
    transformer = CodeTransformer()
    transformer.run()
