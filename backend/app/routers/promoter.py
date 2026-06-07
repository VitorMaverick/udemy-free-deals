from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models import Category, Course, PromotionLog
from app.schemas import (
    CategoryCreate, CategoryOut, CategoryUpdate,
    CourseCategoryRequest, CourseOut, PromotionLogOut,
)
from app.services.promoter import promote_new_courses

router = APIRouter(prefix="/api/admin", tags=["promoter"])


# --- Categories CRUD ---
@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(_: str = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.name))
    return [CategoryOut.model_validate(c) for c in result.scalars().all()]


@router.post("/categories", response_model=CategoryOut)
async def create_category(body: CategoryCreate, _: str = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    cat = Category(**body.model_dump())
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return CategoryOut.model_validate(cat)


@router.put("/categories/{id}", response_model=CategoryOut)
async def update_category(id: str, body: CategoryUpdate, _: str = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.id == id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(cat, key, val)
    cat.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(cat)
    return CategoryOut.model_validate(cat)


@router.delete("/categories/{id}")
async def delete_category(id: str, _: str = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.id == id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    # Check if courses use this category
    count = (await db.execute(select(func.count(Course.id)).where(Course.category_id == id))).scalar() or 0
    if count > 0:
        raise HTTPException(status_code=400, detail=f"{count} cursos usam esta categoria. Remova a associação primeiro.")
    await db.delete(cat)
    await db.commit()
    return {"ok": True}


# --- Course category assignment ---
@router.put("/courses/{course_id}/category", response_model=CourseOut)
async def set_course_category(
    course_id: str, body: CourseCategoryRequest,
    _: str = Depends(get_current_admin), db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    course.category_id = body.category_id
    course.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(course)
    return CourseOut.model_validate(course)


# --- Promoter execution ---
@router.post("/promoter/run")
async def run_promoter(background_tasks: BackgroundTasks, _: str = Depends(get_current_admin)):
    background_tasks.add_task(promote_new_courses)
    return {"message": "Promoter iniciado em background"}


# --- Promotion logs ---
@router.get("/promotion-logs", response_model=list[PromotionLogOut])
async def get_promotion_logs(
    platform: str | None = None,
    status: str | None = None,
    limit: int = Query(50, le=200),
    _: str = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(PromotionLog).order_by(PromotionLog.sent_at.desc())
    if platform:
        query = query.where(PromotionLog.platform == platform)
    if status:
        query = query.where(PromotionLog.status == status)
    result = await db.execute(query.limit(limit))
    return [PromotionLogOut.model_validate(l) for l in result.scalars().all()]


# --- Search Telegram (mock) ---
@router.post("/search-telegram")
async def search_telegram(body: dict, _: str = Depends(get_current_admin)):
    keyword = body.get("keyword", "")
    if not keyword:
        raise HTTPException(status_code=400, detail="keyword é obrigatório")
    from app.services.community_finder import search_telegram_communities
    return await search_telegram_communities(keyword)


# --- Discover communities for a category ---
@router.post("/categories/{id}/discover-communities")
async def discover_communities(id: str, _: str = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.id == id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    from app.services.community_finder import search_telegram_communities, search_reddit_communities
    keyword = cat.name

    telegram = await search_telegram_communities(keyword)
    reddit = await search_reddit_communities(keyword)

    # Salvar nos campos discovered
    cat.discovered_telegram = telegram
    cat.discovered_reddit = reddit
    cat.updated_at = datetime.utcnow()
    await db.commit()

    return {"telegram": telegram, "reddit": reddit}


# --- Add discovered community to active list ---
@router.post("/categories/{id}/add-community")
async def add_community(id: str, body: dict, _: str = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.id == id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    platform = body.get("platform")  # 'telegram' or 'reddit'
    value = body.get("value")  # channel username or subreddit name

    if platform == "telegram" and value:
        channels = list(cat.telegram_channels or [])
        if value not in channels:
            channels.append(value)
            cat.telegram_channels = channels
    elif platform == "reddit" and value:
        subs = list(cat.subreddits or [])
        if value not in subs:
            subs.append(value)
            cat.subreddits = subs
    else:
        raise HTTPException(status_code=400, detail="platform e value obrigatórios")

    cat.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(cat)
    return {"ok": True, "telegram_channels": cat.telegram_channels, "subreddits": cat.subreddits}


# --- Trending posts for a category ---
@router.post("/categories/{id}/trending-posts")
async def get_trending_posts(id: str, _: str = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.id == id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    from app.services.trending_posts import fetch_trending_twitter, fetch_trending_reddit

    keywords = cat.twitter_keywords or [cat.name]
    subreddits = cat.subreddits or None

    twitter_posts = await fetch_trending_twitter(keywords)
    reddit_posts = await fetch_trending_reddit(keywords, subreddits)

    return {"twitter": twitter_posts, "reddit": reddit_posts}


# --- Generate comment for a trending post ---
@router.post("/trending-posts/comment")
async def gen_comment(body: dict, _: str = Depends(get_current_admin)):
    from app.services.trending_posts import generate_comment
    comment = generate_comment(
        post=body.get("post", {}),
        course_title=body.get("course_title", ""),
        category_name=body.get("category_name", ""),
        affiliate_link=body.get("affiliate_link", ""),
    )
    return {"comment": comment, "post_url": body.get("post", {}).get("url", "")}
