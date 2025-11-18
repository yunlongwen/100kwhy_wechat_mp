from contextlib import asynccontextmanager
from datetime import datetime
import os
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from loguru import logger

from .notifier.wecom import build_wecom_digest_markdown, send_markdown_to_wecom
from .routes import wechat
from .sources.ai_articles import pick_daily_ai_articles, todays_theme

# 全局 scheduler 实例
scheduler: Optional[AsyncIOScheduler] = None


def _get_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning(f"Invalid int value for env {name}={raw!r}, fallback to {default}.")
        return default


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时启动 scheduler，关闭时关闭 scheduler"""
    global scheduler

    digest_hour = _get_int_env("DAILY_DIGEST_HOUR", 14)
    digest_minute = _get_int_env("DAILY_DIGEST_MINUTE", 0)
    digest_count = _get_int_env("DAILY_DIGEST_COUNT", 5)

    # 启动时
    scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

    @scheduler.scheduled_job("cron", hour=digest_hour, minute=digest_minute)
    async def job_send_daily_ai_digest() -> None:
        """Send AI coding articles digest to WeCom group."""
        now = datetime.now()
        articles = pick_daily_ai_articles(k=digest_count)
        if not articles:
            logger.warning("No AI articles available for today, skip sending.")
            return

        theme = todays_theme(now)
        date_str = now.strftime("%Y-%m-%d")
        items = [
            {
                "title": a.title,
                "url": a.url,
                "source": a.source,
                "summary": a.summary,
            }
            for a in articles
        ]

        content = build_wecom_digest_markdown(date_str=date_str, theme=theme, items=items)
        logger.info("Sending daily AI digest to WeCom group...")
        await send_markdown_to_wecom(content)

    scheduler.start()
    logger.info(
        "Scheduler started. Daily digest will be sent at %02d:%02d (Asia/Shanghai), "
        "with up to %d articles.",
        digest_hour,
        digest_minute,
        digest_count,
    )

    yield  # 应用运行期间

    # 关闭时
    if scheduler:
        scheduler.shutdown()
        logger.info("Scheduler stopped.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="100kwhy WeChat MP Backend",
        lifespan=lifespan,
    )

    app.include_router(wechat.router, prefix="/wechat", tags=["wechat"])

    return app


app = create_app()


