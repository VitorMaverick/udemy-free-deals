"""Crawler que coleta cursos gratuitos da Udemy de fontes agregadoras de cupons."""

import asyncio
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode

import httpx
from bs4 import BeautifulSoup
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from app.models import Course

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
]

# Fontes de cupons gratuitos
SOURCES = [
    "https://www.real.discount/udemy-coupon-code/?couponType=100percentoff&page=1",
    "https://www.real.discount/udemy-coupon-code/?couponType=100percentoff&page=2",
]


def make_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:200]


def build_affiliate_url(coupon_url: str) -> str:
    """Adiciona tag de afiliado Impact ao link."""
    if not settings.affiliate_tag:
        return coupon_url
    base = f"https://www.udemy.com/course/{coupon_url.split('/course/')[-1]}" if "/course/" in coupon_url else coupon_url
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}referralCode={settings.affiliate_tag}"


async def fetch_page(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        resp = await client.get(url, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        return resp.text
    except httpx.HTTPError as e:
        logger.warning(f"Falha ao buscar {url}: {e}")
        return None


async def parse_real_discount(html: str) -> list[dict]:
    """Parseia cursos do real.discount."""
    soup = BeautifulSoup(html, "lxml")
    courses = []

    cards = soup.select("div.card, li.card-item, div.coupon-card, a[href*='udemy.com/course']")

    # Fallback: buscar todos os links para udemy
    if not cards:
        links = soup.find_all("a", href=re.compile(r"udemy\.com/course/"))
        for link in links:
            href = link.get("href", "")
            title = link.get_text(strip=True) or link.get("title", "")
            if not title or len(title) < 5:
                continue

            img = link.find("img")
            image_url = img.get("src", "") if img else ""

            courses.append({
                "title": title[:500],
                "coupon_url": href,
                "image_url": image_url,
                "is_free": True,
                "discount_percent": 100,
                "original_price": 0,
                "discount_price": 0,
            })
    else:
        for card in cards:
            link_el = card if card.name == "a" else card.find("a", href=re.compile(r"udemy\.com"))
            if not link_el:
                continue
            href = link_el.get("href", "")
            title_el = card.find(["h3", "h4", "h5", "span.title", "div.title"])
            title = title_el.get_text(strip=True) if title_el else link_el.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            img = card.find("img")
            image_url = img.get("src", "") if img else ""

            courses.append({
                "title": title[:500],
                "coupon_url": href,
                "image_url": image_url,
                "is_free": True,
                "discount_percent": 100,
                "original_price": 0,
                "discount_price": 0,
            })

    return courses


async def save_courses(courses_data: list[dict], session: AsyncSession) -> int:
    """Salva cursos no banco, evitando duplicatas por título."""
    saved = 0
    for data in courses_data:
        slug = make_slug(data["title"])
        existing = await session.execute(select(Course).where(Course.slug == slug))
        if existing.scalar_one_or_none():
            continue

        course = Course(
            title=data["title"],
            slug=slug,
            image_url=data.get("image_url", ""),
            coupon_url=data["coupon_url"],
            affiliate_url=build_affiliate_url(data["coupon_url"]),
            is_free=data.get("is_free", True),
            discount_percent=data.get("discount_percent", 100),
            original_price=data.get("original_price", 0),
            discount_price=data.get("discount_price", 0),
            collected_at=datetime.utcnow(),
        )
        session.add(course)
        saved += 1

    await session.commit()
    return saved


async def run_crawler() -> dict:
    """Executa o crawler em todas as fontes configuradas."""
    logger.info("Iniciando crawler...")
    total_found = 0
    total_saved = 0

    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENTS[0]}) as client:
        for source_url in SOURCES:
            html = await fetch_page(client, source_url)
            if not html:
                continue

            courses_data = await parse_real_discount(html)
            total_found += len(courses_data)

            async with async_session() as session:
                saved = await save_courses(courses_data, session)
                total_saved += saved

            # Rate limiting ético
            await asyncio.sleep(3)

    logger.info(f"Crawler finalizado: {total_found} encontrados, {total_saved} novos salvos")
    return {"found": total_found, "saved": total_saved}


async def deactivate_expired() -> int:
    """Desativa cursos com cupom expirado."""
    async with async_session() as session:
        result = await session.execute(
            select(Course).where(
                Course.is_active == True,
                Course.expires_at != None,
                Course.expires_at < datetime.utcnow(),
            )
        )
        expired = result.scalars().all()
        for course in expired:
            course.is_active = False
        await session.commit()
        return len(expired)
