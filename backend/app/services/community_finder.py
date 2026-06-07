"""Serviço de descoberta de comunidades (Telegram, Reddit) por palavra-chave."""

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from app.config import settings


async def search_telegram_communities(keyword: str) -> list[dict]:
    """Busca canais públicos do Telegram via scraping do t.me/s/."""
    results = []
    url = f"https://t.me/s/{keyword}"
    search_url = f"https://tgstat.com/search?q={keyword}&type=channels"

    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0.0.0"}

    try:
        async with httpx.AsyncClient(headers=headers, timeout=15) as client:
            # Tentar tgstat (agregador de canais Telegram)
            resp = await client.get(search_url, follow_redirects=True)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "lxml")
                cards = soup.select("a[href*='t.me/'], .peer-item, .channel-card")
                for card in cards[:15]:
                    name_el = card.select_one(".channel-name, .peer-title, h4, h3")
                    name = name_el.get_text(strip=True) if name_el else card.get_text(strip=True)[:60]
                    href = card.get("href", "")
                    username = ""
                    if "t.me/" in href:
                        username = "@" + href.split("t.me/")[-1].split("/")[0].split("?")[0]
                    members_el = card.select_one(".counter, .members, .subscribers")
                    members = int("".join(filter(str.isdigit, members_el.get_text()))) if members_el else 0

                    if username and len(username) > 2:
                        results.append({"username": username, "title": name[:100], "members": members})

            if not results:
                # Fallback: sugestões baseadas em padrões comuns
                results = _generate_telegram_suggestions(keyword)

    except Exception as e:
        logger.warning(f"[COMMUNITY_FINDER] Telegram search error: {e}")
        results = _generate_telegram_suggestions(keyword)

    return results[:10]


def _generate_telegram_suggestions(keyword: str) -> list[dict]:
    """Gera sugestões de canais baseadas em padrões comuns."""
    kw = keyword.lower().replace(" ", "")
    return [
        {"username": f"@{kw}_courses", "title": f"Cursos de {keyword}", "members": 0},
        {"username": f"@free_{kw}", "title": f"Free {keyword}", "members": 0},
        {"username": f"@{kw}_br", "title": f"{keyword} Brasil", "members": 0},
        {"username": f"@learn{kw}", "title": f"Learn {keyword}", "members": 0},
    ]


async def search_reddit_communities(keyword: str) -> list[dict]:
    """Busca subreddits por palavra-chave via API pública do Reddit."""
    results = []
    url = f"https://www.reddit.com/subreddits/search.json?q={keyword}&limit=15"
    headers = {"User-Agent": settings.reddit_user_agent}

    try:
        async with httpx.AsyncClient(headers=headers, timeout=15) as client:
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code == 200:
                data = resp.json()
                for child in data.get("data", {}).get("children", []):
                    sub = child.get("data", {})
                    results.append({
                        "name": sub.get("display_name", ""),
                        "title": sub.get("title", "")[:100],
                        "subscribers": sub.get("subscribers", 0),
                        "description": sub.get("public_description", "")[:200],
                    })
    except Exception as e:
        logger.warning(f"[COMMUNITY_FINDER] Reddit search error: {e}")

    return results[:10]


async def search_discord_servers(keyword: str) -> list[dict]:
    """Placeholder - descoberta de servidores Discord não é suportada nativamente."""
    return [{"note": f"Busque manualmente em disboard.org/search?keyword={keyword}"}]
