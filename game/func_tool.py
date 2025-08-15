import random
import json
import os
from pathlib import Path
from request.google_chat import google_request
from request.logger_setup import logger
from request.model import ChatRequest

#@lru_cache(maxsize=1)
def read_system_prompt() -> str:
    """Read system prompt text with robust path resolution and caching.

    Resolution order:
    1) Env var `SYSTEM_PROMPT_PATH` (absolute or relative to project root)
    2) Default: `<project_root>/prompt/desription.txt`
    """
    try:
        project_root = Path(__file__).resolve().parent.parent
        env_path = os.getenv("SYSTEM_PROMPT_PATH")

        if env_path:
            candidate_path = Path(env_path)
            if not candidate_path.is_absolute():
                candidate_path = project_root / candidate_path
        else:
            candidate_path = project_root / "prompt" / "description.txt"

        content = candidate_path.read_text(encoding="utf-8")
        if not content.strip():
            logger.warning("System prompt file is empty: %s", candidate_path)
        else:
            logger.info("Loaded system prompt from: %s", candidate_path)
        return content
    except FileNotFoundError:
        logger.error("System prompt file not found. Set SYSTEM_PROMPT_PATH or ensure default exists at 'prompt/desription.txt'.")
        return ""
    except Exception as exc:
        logger.exception("Failed to read system prompt: %s", exc)
        return ""

async def send_to_google_ai(message, session_id):
    req = ChatRequest(
        prompt=message,
        session_id=session_id,
        system_prompt=read_system_prompt(),
        #tools_declaration=tools_declaration
    )
    
    resp = await google_request(req)
    return resp

def perform_d100_check(success_rate: int) -> str:
    """
    Performs a D100 check, including rules for critical success and failure.

    - A roll of 1 is a 'Critical Success'.
    - A roll of 100 is a 'Critical Failure'.
    - Otherwise, the result is determined by the success_rate.

    Args:
        success_rate: The probability of success (1-100).

    Returns:
        A JSON string containing the roll result, check status, and the success rate used.
    """
    if not 1 <= success_rate <= 100:
        return "Success rate must be between 1 and 100."

    roll_result = random.randint(1, 100)
    status = ""

    # Priority check for critical success and failure
    if roll_result == 1:
        status = f"🎲擲骰大成功, 成功率:{success_rate}"
    elif roll_result == 100:
        status = f"🎲擲骰大失敗, 成功率:{success_rate}"
    # Standard check if not a critical roll
    elif roll_result <= success_rate:
        status = f"🎲擲骰成功, 成功率:{success_rate}"
    else:
        status = f"🎲擲骰失敗, 成功率:{success_rate}"
    
    return status