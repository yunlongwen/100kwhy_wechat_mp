import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from random import sample
from typing import List, Optional

from loguru import logger


@dataclass
class AiArticle:
    title: str
    url: str
    source: str
    summary: str


def _config_path() -> Path:
    """
    Get path to config/ai_articles.json relative to project root.
    """
    # app/sources/ai_articles.py -> project_root/config/ai_articles.json
    return Path(__file__).resolve().parents[2] / "config" / "ai_articles.json"


def load_ai_articles_pool() -> List[AiArticle]:
    """
    Load a pool of high-quality AI coding articles from JSON config file.

    Config file: config/ai_articles.json
    Structure:
      [
        {
          "title": "...",
          "url": "...",
          "source": "...",
          "summary": "..."
        },
        ...
      ]
    """
    path = _config_path()
    if not path.exists():
        logger.warning(f"AI articles config not found at {path}, return empty list.")
        return []

    try:
        with path.open("r", encoding="utf-8") as f:
            raw_items = json.load(f)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Failed to load AI articles config: {exc}")
        return []

    articles: List[AiArticle] = []
    for item in raw_items:
        try:
            articles.append(
                AiArticle(
                    title=item.get("title", "").strip(),
                    url=item.get("url", "").strip(),
                    source=item.get("source", "").strip(),
                    summary=item.get("summary", "").strip(),
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Invalid article item in config: {item}, error: {exc}")

    return articles


def pick_daily_ai_articles(k: int = 5) -> List[AiArticle]:
    pool = load_ai_articles_pool()
    if len(pool) <= k:
        return pool
    return sample(pool, k)


def todays_theme(now: Optional[datetime] = None) -> str:
    # 简单占位：后续可以根据星期 / 最近热点等自动生成主题
    return "AI 编程效率与工程实践精选"


