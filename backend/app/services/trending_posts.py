"""Serviço de busca de posts com alto engajamento (Twitter/Reddit)."""

import httpx
from loguru import logger

from app.config import settings


async def fetch_trending_twitter(keywords: list[str], limit: int = 10) -> list[dict]:
    """Busca tweets recentes com alto engajamento usando Twitter API v2."""
    bearer = settings.twitter_bearer_token
    if not bearer:
        return [{"error": "TWITTER_BEARER_TOKEN não configurado"}]

    query = " OR ".join(f'"{kw}"' for kw in keywords[:5])
    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": f"{query} -is:retweet lang:en",
        "max_results": min(limit * 3, 100),  # Buscar mais para filtrar
        "tweet.fields": "public_metrics,created_at,author_id",
        "expansions": "author_id",
        "user.fields": "username,name",
    }
    headers = {"Authorization": f"Bearer {bearer}"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code != 200:
                return [{"error": f"Twitter API: {resp.status_code} - {resp.text[:100]}"}]

            data = resp.json()
            tweets = data.get("data", [])
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

            results = []
            for tweet in tweets:
                metrics = tweet.get("public_metrics", {})
                engagement = metrics.get("like_count", 0) + metrics.get("retweet_count", 0)
                author = users.get(tweet.get("author_id", ""), {})
                results.append({
                    "id": tweet["id"],
                    "text": tweet["text"][:280],
                    "author": author.get("username", ""),
                    "author_name": author.get("name", ""),
                    "likes": metrics.get("like_count", 0),
                    "retweets": metrics.get("retweet_count", 0),
                    "engagement": engagement,
                    "url": f"https://twitter.com/{author.get('username', '_')}/status/{tweet['id']}",
                    "created_at": tweet.get("created_at", ""),
                })

            results.sort(key=lambda x: x["engagement"], reverse=True)
            return results[:limit]

    except Exception as e:
        logger.warning(f"[TRENDING] Twitter error: {e}")
        return [{"error": str(e)[:200]}]


async def fetch_trending_reddit(keywords: list[str], subreddits: list[str] | None = None, limit: int = 10) -> list[dict]:
    """Busca posts do Reddit com alto engajamento via API pública."""
    headers = {"User-Agent": settings.reddit_user_agent}
    results = []

    # Buscar em subreddits específicos ou geral
    search_targets = []
    if subreddits:
        for sub in subreddits[:3]:
            search_targets.append(f"https://www.reddit.com/r/{sub}/search.json?q={'+'.join(keywords[:3])}&sort=top&t=week&limit=10")
    else:
        query = "+".join(keywords[:3])
        search_targets.append(f"https://www.reddit.com/search.json?q={query}&sort=top&t=week&limit=20")

    try:
        async with httpx.AsyncClient(headers=headers, timeout=15) as client:
            for url in search_targets:
                resp = await client.get(url, follow_redirects=True)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                for child in data.get("data", {}).get("children", []):
                    post = child.get("data", {})
                    results.append({
                        "id": post.get("id", ""),
                        "title": post.get("title", "")[:200],
                        "subreddit": post.get("subreddit", ""),
                        "author": post.get("author", ""),
                        "score": post.get("score", 0),
                        "num_comments": post.get("num_comments", 0),
                        "url": f"https://reddit.com{post.get('permalink', '')}",
                        "created_utc": post.get("created_utc", 0),
                    })
    except Exception as e:
        logger.warning(f"[TRENDING] Reddit error: {e}")

    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results[:limit]


def generate_comment(post: dict, course_title: str, category_name: str, affiliate_link: str) -> str:
    """Gera um comentário sugerido para o admin postar manualmente."""
    templates = [
        f"Ótimo conteúdo! Quem se interessa por {category_name} pode conferir este curso gratuito (link válido por tempo limitado): {affiliate_link}",
        f"Conteúdo muito relevante! Falando em {category_name}, achei este curso 100% gratuito na Udemy: {affiliate_link}",
        f"Excelente discussão! Para quem quer se aprofundar em {category_name}, tem este curso gratuito disponível agora: {affiliate_link}",
    ]
    import random
    return random.choice(templates)
