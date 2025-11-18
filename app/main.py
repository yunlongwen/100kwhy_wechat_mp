from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from loguru import logger

from .notifier.wecom import build_wecom_digest_markdown, send_markdown_to_wecom
from .routes import wechat
from .sources.ai_articles import pick_daily_ai_articles, todays_theme


def create_app() -> FastAPI:
    app = FastAPI(title="100kwhy WeChat MP Backend")

    app.include_router(wechat.router, prefix="/wechat", tags=["wechat"])

    scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

    @scheduler.scheduled_job("cron", hour=14, minute=0)
    async def job_send_daily_ai_digest() -> None:
        """Every day at 14:00, send 5 AI coding articles to WeCom group."""
        now = datetime.now()
        articles = pick_daily_ai_articles(k=5)
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

    return app


app = create_app()


