import os


def get_default_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def get_timeout_seconds() -> float:
    raw = os.getenv("HTTP_TIMEOUT_SECONDS", "60")
    try:
        return float(raw)
    except Exception:
        return 60.0


def get_max_retries() -> int:
    raw = os.getenv("HTTP_MAX_RETRIES", "2")
    try:
        return int(raw)
    except Exception:
        return 2


def get_retry_backoff_base() -> float:
    raw = os.getenv("HTTP_RETRY_BACKOFF_BASE", "0.8")
    try:
        return float(raw)
    except Exception:
        return 0.8



