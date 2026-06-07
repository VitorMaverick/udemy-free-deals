"""APScheduler para rodar o crawler periodicamente."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app.config import settings
from app.crawler.udemy_crawler import run_crawler

scheduler = AsyncIOScheduler()


async def crawler_job():
    logger.info("Job: executando crawler agendado")
    await run_crawler()


def start_scheduler():
    scheduler.add_job(
        crawler_job, "interval",
        hours=settings.crawler_interval_hours,
        id="crawler_job", replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler iniciado: crawler a cada {settings.crawler_interval_hours}h")
