import json
from dataclasses import dataclass
from pathlib import Path

from loguru import logger


def _project_root() -> Path:
    # app/config_loader.py -> project_root
    return Path(__file__).resolve().parents[1]


@dataclass
class DigestSchedule:
    hour: int = 14
    minute: int = 0
    count: int = 5


def _digest_schedule_path() -> Path:
    return _project_root() / "config" / "digest_schedule.json"


def load_digest_schedule() -> DigestSchedule:
    """
    Load daily digest schedule from config/digest_schedule.json.

    Example:
    {
      "hour": 14,
      "minute": 0,
      "count": 5
    }
    """
    path = _digest_schedule_path()
    default = DigestSchedule()

    if not path.exists():
        logger.warning(f"Digest schedule config not found at {path}, using defaults: {default}.")
        return default

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Failed to load digest schedule config: {exc}, using defaults: {default}.")
        return default

    def _get_int(name: str, fallback: int) -> int:
        raw = data.get(name)
        if raw is None:
            return fallback
        try:
            return int(raw)
        except (TypeError, ValueError):
            logger.warning(f"Invalid value for digest schedule {name}={raw!r}, fallback to {fallback}.")
            return fallback

    schedule = DigestSchedule(
        hour=_get_int("hour", default.hour),
        minute=_get_int("minute", default.minute),
        count=_get_int("count", default.count),
    )

    return schedule


