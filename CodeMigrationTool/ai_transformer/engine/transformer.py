import os
from .utils import (
    load_prompt,
    render_prompt,
    call_model,
    clean_generated_code,
    save_output_file,
    load_config,
    load_all_contexts
)
from .coverage_checker import check_coverage
from .logger import get_logger

logger = get_logger()


class CodeTransformer:
    def __init__(self, config_path='config.yml'):
        self.config = load_config(config_path)
        self.source_dir = self.config['source_code_base']
        self.output_dir = self.config['output_dir']
        self.prompt_dir = self.config['prompt_dir']
        self.llm_settings = self.config['llm_settings']
        self.primary_model = self.config['primary_model']
        self.reviewer_model = self.config['reviewer_model']

        os.makedirs(self.output_dir, exist_ok=True)

        self.context_data = load_all_contexts(self.config)

        # Load prompts
        self.transform_prompt = load_prompt(os.path.join(self.prompt_dir, "transform_class.prompt"))
        self.review_prompt = load_prompt(os.path.join(self.prompt_dir, "review_coverage.prompt"))
        self.feedback_prompt = load_prompt(os.path.join(self.prompt_dir, "apply_feedback.prompt"))

    def transform_file(self, class_name, file_meta, file_content):
        context_id = f"{class_name}"

        if "relative_path" not in file_meta:
            logger.error(f"[{context_id}] 'relative_path' missing in file_meta: {file_meta}")
        if "absolute_path" not in file_meta:
            logger.error(f"[{context_id}] 'absolute_path' missing in file_meta: {file_meta}")

        logger.info(f"[{context_id}] Transforming file {file_meta['relative_path']}")

        # Step 1: Primary model transformation
        prompt = render_prompt(self.transform_prompt, {
            "context": f"class: {class_name}, path: {file_meta['relative_path']}",
            "source_code": file_content
        })
        raw_response = call_model(prompt, self.primary_model, self.llm_settings)
        transformed_code = clean_generated_code(raw_response)

        save_output_file(transformed_code, class_name, self.output_dir, suffix="_v1")

        # Step 2: Reviewer model coverage check
        coverage, issues = check_coverage(
            source_code=file_content,
            generated_code=transformed_code,
            reviewer_model=self.reviewer_model,
            llm_settings=self.llm_settings,
            prompt_dir=self.prompt_dir,
            context_id=context_id
        )

        iteration = 1
        while coverage < 99 and iteration <= 3:
            logger.warning(f"[{context_id}] Coverage {coverage}%. Iteration {iteration}...")

            feedback_prompt = render_prompt(self.feedback_prompt, {
                "source_code": file_content,
                "generated_code": transformed_code,
                "feedback": "\n".join(issues)
            })
            feedback_response = call_model(feedback_prompt, self.primary_model, self.llm_settings)
            transformed_code = clean_generated_code(feedback_response)

            save_output_file(transformed_code, class_name, self.output_dir, suffix=f"_v{iteration + 1}")

            coverage, issues = check_coverage(
                source_code=file_content,
                generated_code=transformed_code,
                reviewer_model=self.reviewer_model,
                llm_settings=self.llm_settings,
                prompt_dir=self.prompt_dir,
                context_id=context_id
            )

            iteration += 1

        logger.info(f"[{context_id}] Final coverage: {coverage}%")
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
    transformer = CodeTransformer()  # default config path
    transformer.run()
