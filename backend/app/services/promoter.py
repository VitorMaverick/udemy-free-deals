"""Módulo promotor: envia cursos para canais de divulgação (Telegram, Discord)."""

import asyncio
import random
from datetime import datetime

import httpx
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from app.models import Category, Course, PromotionLog


def _build_promotion_message(course: Course) -> str:
    """Monta mensagem de divulgação formatada."""
    price_display = "🆓 GRÁTIS" if course.is_free else f"R${course.discount_price:.2f}"
    original = f"~R${course.original_price:.2f}~" if course.original_price > 0 else ""

    msg = (
        f"🎓 *{course.title}*\n\n"
        f"👨‍🏫 {course.instructor}\n" if course.instructor else ""
    )
    msg = f"🎓 *{course.title}*\n\n"
    if course.instructor:
        msg += f"👨‍🏫 Instrutor: {course.instructor}\n"
    if course.description:
        msg += f"📝 {course.description[:150]}\n"
    msg += f"\n💰 {original} → {price_display}\n"
    if course.rating > 0:
        msg += f"⭐ {course.rating:.1f} ({course.students_count} alunos)\n"
    msg += f"\n🔗 {course.affiliate_link or course.udemy_url}\n"
    msg += "\n#UdemyGratis #CursoFree #Udemy"
    return msg


async def post_to_discord(webhook_url: str, course: Course) -> tuple[bool, str]:
    """Envia mensagem para webhook do Discord."""
    message = _build_promotion_message(course).replace("*", "**")  # Discord usa ** para bold
    payload = {"content": message}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(webhook_url, json=payload, timeout=15)
            if resp.status_code in (200, 204):
                logger.info(f"[PROMOTER] Discord OK: {webhook_url[:50]}")
                return True, ""
            return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
    except Exception as e:
        return False, str(e)[:200]


async def post_to_telegram(channel: str, course: Course) -> tuple[bool, str]:
    """Envia mensagem para canal do Telegram via Bot API."""
    bot_token = settings.telegram_bot_token
    if not bot_token:
        return False, "TELEGRAM_BOT_TOKEN não configurado"

    message = _build_promotion_message(course)
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": channel,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=15)
            data = resp.json()
            if data.get("ok"):
                logger.info(f"[PROMOTER] Telegram OK: {channel}")
                return True, ""
            return False, data.get("description", "Unknown error")
    except Exception as e:
        return False, str(e)[:200]


async def post_to_twitter(message: str) -> tuple[bool, str]:
    """Esqueleto - Twitter não implementado ainda."""
    logger.info("[PROMOTER] Twitter not implemented yet")
    return False, "Not implemented"


async def post_to_reddit(subreddit: str, title: str, content: str) -> tuple[bool, str]:
    """Esqueleto - Reddit não implementado ainda."""
    logger.info("[PROMOTER] Reddit not implemented yet")
    return False, "Not implemented"


def search_telegram_channels(keyword: str) -> list[dict]:
    """Mock: retorna sugestões de canais baseadas na keyword."""
    suggestions = {
        "python": ["@pythonbrasil", "@cursospython", "@pythonfree", "@learnpython_channel"],
        "javascript": ["@javascriptbr", "@js_courses", "@webdevfree"],
        "design": ["@designfree", "@uxui_courses", "@graphicdesign_free"],
        "data": ["@datascience_free", "@machinelearning_br", "@bigdata_courses"],
        "marketing": ["@marketingdigital_br", "@socialmedia_free"],
    }
    keyword_lower = keyword.lower()
    for key, channels in suggestions.items():
        if key in keyword_lower:
            return [{"username": ch, "title": f"Canal {ch}", "members": random.randint(500, 50000)} for ch in channels]
    # Genérico
    return [
        {"username": f"@{keyword_lower}_courses", "title": f"Cursos de {keyword}", "members": random.randint(100, 5000)},
        {"username": f"@free_{keyword_lower}", "title": f"Free {keyword}", "members": random.randint(100, 5000)},
    ]


async def promote_course(course: Course, session: AsyncSession) -> int:
    """Promove um curso em todos os canais da sua categoria. Retorna quantidade de envios."""
    if not course.category_id:
        return 0

    result = await session.execute(select(Category).where(Category.id == course.category_id))
    cat = result.scalar_one_or_none()
    if not cat or not cat.is_active:
        return 0

    sent = 0

    # Discord webhooks
    for webhook in (cat.discord_webhooks or []):
        success, error = await post_to_discord(webhook, course)
        session.add(PromotionLog(
            course_id=course.id, platform="discord",
            target=webhook[:255], status="success" if success else "failed",
            error_message=error,
        ))
        sent += 1 if success else 0
        await asyncio.sleep(random.uniform(3, 8))

    # Telegram channels
    for channel in (cat.telegram_channels or []):
        success, error = await post_to_telegram(channel, course)
        session.add(PromotionLog(
            course_id=course.id, platform="telegram",
            target=channel, status="success" if success else "failed",
            error_message=error,
        ))
        sent += 1 if success else 0
        await asyncio.sleep(random.uniform(5, 15))

    await session.commit()
    return sent


async def promote_new_courses():
    """Busca cursos publicados não promovidos e executa a divulgação."""
    logger.info("[PROMOTER] Iniciando divulgação de cursos...")

    async with async_session() as session:
        result = await session.execute(
            select(Course).where(
                Course.status == "published",
                Course.promoted_at == None,
                Course.category_id != None,
                Course.affiliate_link != "",
            ).order_by(Course.detected_at.asc())
        )
        courses = result.scalars().all()

        if not courses:
            logger.info("[PROMOTER] Nenhum curso novo para promover")
            return {"promoted": 0, "total_sent": 0}

        total_sent = 0
        for course in courses:
            sent = await promote_course(course, session)
            course.promoted_at = datetime.utcnow()
            total_sent += sent
            await asyncio.sleep(random.uniform(2, 5))

        await session.commit()
        logger.info(f"[PROMOTER] Concluído: {len(courses)} cursos, {total_sent} envios")
        return {"promoted": len(courses), "total_sent": total_sent}
