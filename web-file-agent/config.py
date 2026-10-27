"""Environment-backed configuration for the demo agent."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _positive_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
        return value if value > 0 else default
    except (TypeError, ValueError):
        return default


API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")
MODEL = os.getenv("OPENAI_MODEL", "").strip()
WORKSPACE = Path(os.getenv("AGENT_WORKSPACE", "./workspace")).expanduser().resolve()
MAX_STEPS = _positive_int("MAX_STEPS", 8)
REQUEST_TIMEOUT = _positive_int("REQUEST_TIMEOUT", 20)
MAX_FILE_BYTES = _positive_int("MAX_FILE_BYTES", 1_000_000)
MAX_WEB_BYTES = _positive_int("MAX_WEB_BYTES", 1_000_000)
