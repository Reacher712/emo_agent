"""Paths shared by the original application, independent of the checkout location."""

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
MODEL_DIR = PROJECT_DIR / "EmoLLM" / "model"
OUTPUT_DIR = PROJECT_DIR / "outputs"
DELIVERABLES_DIR = PROJECT_DIR / "deliverables"
PROMPT_CSV = PROJECT_DIR / "emotion_to_prompt.csv"
LOG_CSV = OUTPUT_DIR / "smoke_test_log.csv"


def load_project_env() -> None:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_DIR / ".env", override=False)
