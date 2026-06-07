"""
Crawler que busca cursos gratuitos da Udemy de múltiplas fontes.
Fontes: API Udemy (se disponível), discudemy.com, coursevania.com, real.discount
"""

import asyncio
import re
import random
from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models import Course, Log

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
]

# Fontes de cursos gratuitos
SOURCES = [
    {"name": "discudemy", "url": "https://www.discudemy.com/all/1"},
    {"name": "discudemy_p2", "url": "https://www.discudemy.com/all/2"},
    {"name": "coursevania", "url": "https://coursevania.com/courses/"},
    {"name": "real_discount", "url": "https://www.real.discount/udemy-coupon-code/?couponType=100percentoff&page=1"},
]


def make_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:200]


async def save_log(session: AsyncSession, level: str, message: str):
    """Salva log no banco e imprime no console."""
    log = Log(agent_name="crawler", level=level, message=message)
    session.add(log)
    if level == "ERROR":
        logger.error(f"[CRAWLER] {message}")
    else:
        logger.info(f"[CRAWLER] {message}")


async def fetch_page(client: httpx.AsyncClient, url: str) -> str | None:
    """Busca página HTML com tratamento de erro."""
    try:
        resp = await client.get(url, follow_redirects=True, timeout=30)
        if resp.status_code == 200:
            return resp.text
        logger.warning(f"[CRAWLER] {url} retornou status {resp.status_code}")
        return None
    except httpx.HTTPError as e:
        logger.warning(f"[CRAWLER] Erro ao buscar {url}: {e}")
        return None


async def parse_discudemy(client: httpx.AsyncClient, html: str) -> list[dict]:
    """Parseia cursos do discudemy.com / couponami.com.
    Fluxo: listagem → página do curso → /go/ page → URL Udemy com cupom.
    """
    soup = BeautifulSoup(html, "lxml")
    courses = []

    # discudemy/couponami lista cards com links para páginas de detalhe
    cards = soup.select("section.card")
    if not cards:
        cards = soup.select(".card")

    for card in cards[:15]:  # Limitar para respeitar rate limiting
        title_el = card.select_one("h3, h2, .card-title, a")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        if not title or len(title) < 5:
            continue

        link_el = card.select_one("a[href]")
        detail_url = link_el.get("href", "") if link_el else ""
        if not detail_url:
            continue

        img = card.select_one("img")
        image_url = img.get("src", "") or img.get("data-src", "") if img else ""

        cat_el = card.select_one(".category, .badge, small a")
        category = cat_el.get_text(strip=True) if cat_el else ""

        # Seguir a página de detalhe para pegar o link /go/
        udemy_url = ""
        coupon_code = ""
        try:
            await asyncio.sleep(random.uniform(1.0, 2.0))
            detail_html = await fetch_page(client, detail_url)
            if detail_html:
                detail_soup = BeautifulSoup(detail_html, "lxml")
                # Procurar link /go/ (botão "Take Course")
                go_link = detail_soup.select_one("a[href*='/go/']")
                if go_link:
                    go_url = go_link.get("href", "")
                    if go_url:
                        await asyncio.sleep(random.uniform(0.5, 1.5))
                        go_html = await fetch_page(client, go_url)
                        if go_html:
                            go_soup = BeautifulSoup(go_html, "lxml")
                            # Na página /go/, o link da Udemy com cupom está direto
                            udemy_link = go_soup.find("a", href=re.compile(r"udemy\.com/course/"))
                            if udemy_link:
                                udemy_url = udemy_link.get("href", "")
                                # Extrair coupon code da URL
                                match = re.search(r"couponCode=([^&]+)", udemy_url)
                                if match:
                                    coupon_code = match.group(1)
        except Exception as e:
            logger.debug(f"[CRAWLER] Erro ao resolver URL para '{title}': {e}")

        courses.append({
            "title": title[:500],
            "udemy_url": udemy_url,
            "image_url": image_url,
            "category": category,
            "coupon_code": coupon_code,
            "is_free": True,
            "original_price": 0,
            "discount_price": 0,
        })

    return courses


async def parse_coursevania(html: str) -> list[dict]:
    """Parseia cursos do coursevania.com."""
    soup = BeautifulSoup(html, "lxml")
    courses = []

    cards = soup.select("article, .theme-block, .course-item, div.col a[href*='coursevania']")
    if not cards:
        cards = soup.select("a[href*='udemy.com'], a[href*='/course/']")

    for card in cards[:20]:
        title_el = card.select_one("h3, h2, h4, .entry-title, .course-title")
        if not title_el:
            title = card.get_text(strip=True)[:200]
        else:
            title = title_el.get_text(strip=True)

        if not title or len(title) < 5:
            continue

        img = card.select_one("img")
        image_url = img.get("src", "") or img.get("data-src", "") if img else ""

        link_el = card if card.name == "a" else card.select_one("a[href]")
        href = link_el.get("href", "") if link_el else ""

        courses.append({
            "title": title[:500],
            "udemy_url": href if "udemy.com" in href else "",
            "image_url": image_url,
            "category": "",
            "is_free": True,
            "original_price": 0,
            "discount_price": 0,
        })

    return courses


async def parse_real_discount(html: str) -> list[dict]:
    """Parseia cursos do real.discount."""
    soup = BeautifulSoup(html, "lxml")
    courses = []

    # Buscar links para udemy
    links = soup.find_all("a", href=re.compile(r"udemy\.com/course/"))
    for link in links[:20]:
        href = link.get("href", "")
        title = link.get_text(strip=True) or link.get("title", "")
        if not title or len(title) < 5:
            continue

        img = link.find("img")
        image_url = img.get("src", "") if img else ""

        courses.append({
            "title": title[:500],
            "udemy_url": href,
            "image_url": image_url,
            "category": "",
            "is_free": True,
            "original_price": 0,
            "discount_price": 0,
        })

    return courses


async def resolve_udemy_url(client: httpx.AsyncClient, url: str) -> str:
    """Se o URL é de um site intermediário, tenta resolver para URL da Udemy."""
    if "udemy.com/course/" in url:
        return url
    if not url:
        return ""
    # Para sites que fazem redirect para Udemy
    try:
        resp = await client.head(url, follow_redirects=True, timeout=15)
        final_url = str(resp.url)
        if "udemy.com/course/" in final_url:
            return final_url
    except httpx.HTTPError:
        pass
    return url


async def save_courses(courses_data: list[dict], session: AsyncSession, source_name: str) -> int:
    """Salva cursos no banco evitando duplicatas."""
    saved = 0
    for data in courses_data:
        title = data["title"]
        slug = make_slug(title)
        udemy_url = data.get("udemy_url", "")

        # Evitar duplicatas por slug ou udemy_url
        if udemy_url:
            existing = await session.execute(select(Course).where(Course.udemy_url == udemy_url))
        else:
            existing = await session.execute(select(Course).where(Course.slug == slug))
        course = existing.scalar_one_or_none()

        if course:
            if course.status == "expired":
                course.status = "pending"
                course.detected_at = datetime.utcnow()
                saved += 1
                await save_log(session, "INFO", f"Reativado: \"{title}\" ({source_name})")
            continue

        course = Course(
            title=title,
            slug=slug,
            udemy_url=udemy_url,
            image_url=data.get("image_url", ""),
            category=data.get("category", ""),
            coupon_code=data.get("coupon_code", ""),
            instructor=data.get("instructor", ""),
            description=data.get("description", ""),
            rating=float(data.get("rating", 0)),
            students_count=int(data.get("students_count", 0)),
            original_price=float(data.get("original_price", 0)),
            discount_price=float(data.get("discount_price", 0)),
            is_free=data.get("is_free", True),
            status="pending",
            detected_at=datetime.utcnow(),
        )
        session.add(course)
        saved += 1

        price_now = "R$0,00" if data.get("is_free") else f"R${data.get('discount_price', 0):.2f}"
        await save_log(
            session, "INFO",
            f"Novo curso ({source_name}): \"{title}\" - Agora: {price_now}"
        )

    await session.commit()
    return saved


async def run_crawler() -> dict:
    """Executa o crawler em todas as fontes configuradas."""
    logger.info("[CRAWLER] Iniciando busca de cursos gratuitos...")
    total_found = 0
    total_saved = 0

    headers = {"User-Agent": random.choice(USER_AGENTS), "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"}

    async with httpx.AsyncClient(headers=headers) as client:
        async with async_session() as session:
            await save_log(session, "INFO", "Crawler iniciado")
            await session.commit()

        for source in SOURCES:
            source_name = source["name"]
            url = source["url"]
            try:
                html = await fetch_page(client, url)
                if not html:
                    async with async_session() as session:
                        await save_log(session, "ERROR", f"Não foi possível acessar {source_name} ({url})")
                        await session.commit()
                    continue

                # Parsear de acordo com a fonte
                if "discudemy" in source_name:
                    courses_data = await parse_discudemy(client, html)
                elif "coursevania" in source_name:
                    courses_data = await parse_coursevania(html)
                elif "real_discount" in source_name:
                    courses_data = await parse_real_discount(html)
                else:
                    courses_data = []

                total_found += len(courses_data)

                if courses_data:
                    async with async_session() as session:
                        saved = await save_courses(courses_data, session, source_name)
                        total_saved += saved
                        await save_log(session, "INFO", f"{source_name}: {len(courses_data)} encontrados, {saved} novos salvos")
                        await session.commit()
                else:
                    async with async_session() as session:
                        await save_log(session, "INFO", f"{source_name}: 0 cursos encontrados (estrutura pode ter mudado)")
                        await session.commit()

            except Exception as e:
                async with async_session() as session:
                    await save_log(session, "ERROR", f"Erro no crawler ({source_name}): {str(e)[:200]}")
                    await session.commit()

            # Rate limiting ético
            await asyncio.sleep(random.uniform(2.0, 4.0))

    # Log final
    async with async_session() as session:
        await save_log(session, "INFO", f"Crawler finalizado: {total_found} encontrados, {total_saved} novos salvos")
        await session.commit()

    logger.info(f"[CRAWLER] Finalizado: {total_found} encontrados, {total_saved} novos salvos")
    return {"found": total_found, "saved": total_saved}
