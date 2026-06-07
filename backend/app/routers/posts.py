from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Course, Post, PostCourse
from app.schemas import CourseOut, PostOut, PostSummary

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.get("", response_model=list[PostSummary])
async def list_posts(db: AsyncSession = Depends(get_db)):
    """Lista todos os posts (mais recentes primeiro)."""
    result = await db.execute(select(Post).order_by(Post.published_at.desc()).limit(30))
    posts = result.scalars().all()

    summaries = []
    for p in posts:
        count = (await db.execute(
            select(func.count(PostCourse.id)).where(PostCourse.post_id == p.id)
        )).scalar() or 0
        summaries.append(PostSummary(
            id=p.id, slug=p.slug, title=p.title,
            published_at=p.published_at, course_count=count,
        ))
    return summaries


@router.get("/{slug}", response_model=PostOut)
async def get_post(slug: str, db: AsyncSession = Depends(get_db)):
    """Retorna post completo com cursos."""
    result = await db.execute(select(Post).where(Post.slug == slug))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")

    # Buscar cursos do post
    course_ids_result = await db.execute(
        select(PostCourse.course_id).where(PostCourse.post_id == post.id)
    )
    course_ids = course_ids_result.scalars().all()

    courses = []
    if course_ids:
        courses_result = await db.execute(select(Course).where(Course.id.in_(course_ids)))
        courses = [CourseOut.model_validate(c) for c in courses_result.scalars().all()]

    return PostOut(
        id=post.id, slug=post.slug, title=post.title,
        content_html=post.content_html, published_at=post.published_at,
        courses=courses,
    )
