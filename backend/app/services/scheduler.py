"""APScheduler para rodar crawler e promoter periodicamente."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app.config import settings
from app.crawler.udemy_crawler import run_crawler
from app.services.promoter import promote_new_courses

scheduler = AsyncIOScheduler()


async def crawler_job():
    logger.info("Job: executando crawler agendado")
    await run_crawler()


async def promoter_job():
    logger.info("Job: executando promoter agendado")
    await promote_new_courses()


def start_scheduler():
    scheduler.add_job(
        crawler_job, "interval",
        hours=settings.crawler_interval_hours,
        id="crawler_job", replace_existing=True,
    )
    scheduler.add_job(
        promoter_job, "cron",
        hour=10, minute=0,
        id="promoter_job", replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler iniciado: crawler a cada {settings.crawler_interval_hours}h, promoter diário às 10h")
