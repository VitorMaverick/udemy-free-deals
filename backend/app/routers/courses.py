from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Click, Course
from app.schemas import CoursePaginated, CourseOut

router = APIRouter(prefix="/api", tags=["courses"])


@router.get("/courses", response_model=CoursePaginated)
async def list_courses(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: str | None = None,
    language: str | None = None,
    free_only: bool = False,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    # Só mostrar cursos publicados no frontend público
    query = select(Course).where(Course.status == "published")

    if free_only:
        query = query.where(Course.is_free == True)
    if category:
        query = query.where(Course.category == category)
    if language:
        query = query.where(Course.language == language)
    if search:
        query = query.where(Course.title.ilike(f"%{search}%"))

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(Course.detected_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    items = result.scalars().all()

    return CoursePaginated(
        items=[CourseOut.model_validate(c) for c in items],
        total=total, page=page,
        pages=(total + per_page - 1) // per_page if total > 0 else 0,
    )


@router.get("/courses/{slug}", response_model=CourseOut)
async def get_course(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).where(Course.slug == slug, Course.status == "published"))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return CourseOut.model_validate(course)


@router.get("/courses/{id}/redirect")
async def redirect_course(id: str, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).where(Course.id == id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Registrar clique
    click = Click(
        course_id=course.id,
        ip_address=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", "")[:500],
        referer=request.headers.get("referer", "")[:1000],
        clicked_at=datetime.utcnow(),
    )
    db.add(click)
    await db.commit()

    # Redirecionar para affiliate_link se existir, senão udemy_url
    url = course.affiliate_link or course.udemy_url
    return RedirectResponse(url=url, status_code=302)


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Course.category, func.count(Course.id))
        .where(Course.status == "published", Course.category != "")
        .group_by(Course.category)
        .order_by(func.count(Course.id).desc())
    )
    return [{"name": row[0], "count": row[1]} for row in result.all()]


@router.get("/stats")
async def public_stats(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(Course.id)).where(Course.status == "published"))).scalar() or 0
    free = (await db.execute(select(func.count(Course.id)).where(Course.status == "published", Course.is_free == True))).scalar() or 0
    return {"total_courses": total, "free_courses": free}
