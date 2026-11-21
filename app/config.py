import os
from dotenv import load_dotenv

load_dotenv()

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))
TOP_K = int(os.getenv("TOP_K", "5"))
REFUSAL_THRESHOLD = float(os.getenv("REFUSAL_THRESHOLD", "0.5"))
