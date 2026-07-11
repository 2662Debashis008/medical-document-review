from pathlib import Path


class PromptService:
    PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"
    PROMPT_VERSION = "v1"

    DEFAULT_PROMPTS = {
        "prescription_prompt.txt": (
            "You are an expert medical prescription extraction assistant. Return ONLY "
            'one JSON object using schema_version "v2.0" with document_facility, '
            "patient, vitals_anthropometry, history_presenting_complaints_facts, "
            "examination_facts, investigations_facts, medications_facts, "
            "advice_plan_facts, interpretation_inferences, "
            "uncertain_or_illegible_segments, provenance, and admin."
        ),
        "xray_image_prompt.txt": (
            "Analyze the X-ray image and return ONLY one JSON object using "
            'schema_version "xray_v2.0" with patient, xray_study, findings_facts, '
            "impression, advice_plan_facts, and visual_understanding."
        ),
        "xray_report_prompt.txt": (
            "Extract the X-ray report and return ONLY one JSON object using "
            'schema_version "xray_v2.0" with patient, xray_study, findings_facts, '
            "impression, advice_plan_facts, and visual_understanding."
        ),
        "lab_report_prompt.txt": (
            "Extract the laboratory pathology report and return ONLY one JSON object using "
            'schema_version "lab_v1.0" with laboratory, patient, report_date, and panels.'
        ),
    }

    @classmethod
    def ensure_default_prompts(cls):
        cls.PROMPT_DIR.mkdir(parents=True, exist_ok=True)
        for filename, content in cls.DEFAULT_PROMPTS.items():
            path = cls.PROMPT_DIR / filename
            if not path.exists():
                path.write_text(content, encoding="utf-8")

    @classmethod
    def select_prompt_file(cls, document_category: str, file_type: str) -> str:
        if document_category == "prescription":
            return "prescription_prompt.txt"
        if document_category == "lab_report":
            return "lab_report_prompt.txt"
        if file_type == "image":
            return "xray_image_prompt.txt"
        return "xray_report_prompt.txt"

    @classmethod
    def load_prompt(cls, document_category: str, file_type: str) -> tuple[str, str]:
        cls.ensure_default_prompts()
        filename = cls.select_prompt_file(document_category, file_type)
        return (cls.PROMPT_DIR / filename).read_text(encoding="utf-8"), cls.PROMPT_VERSION
