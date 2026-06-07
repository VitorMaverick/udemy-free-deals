from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, get_current_admin, verify_password
from app.database import get_db
from app.models import AdminUser, Click, Course, Log, Post, PostCourse
from app.schemas import (
    AffiliateLinkRequest,
    ClickOut,
    CourseOut,
    DashboardStats,
    LoginRequest,
    LogOut,
    PostOut,
    TokenResponse,
)
from app.crawler.udemy_crawler import run_crawler

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/login", response_model=TokenResponse)
async def admin_login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdminUser).where(AdminUser.username == body.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(user.username))


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(_: str = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(Course.id)))).scalar() or 0
    pending = (await db.execute(select(func.count(Course.id)).where(Course.status == "pending"))).scalar() or 0
    ready = (await db.execute(select(func.count(Course.id)).where(Course.status == "manual_link_created"))).scalar() or 0
    published = (await db.execute(select(func.count(Course.id)).where(Course.status == "published"))).scalar() or 0
    total_clicks = (await db.execute(select(func.count(Click.id)))).scalar() or 0
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    clicks_today = (await db.execute(select(func.count(Click.id)).where(Click.clicked_at >= today))).scalar() or 0
    month_start = today.replace(day=1)
    posts_month = (await db.execute(select(func.count(Post.id)).where(Post.published_at >= month_start))).scalar() or 0

    return DashboardStats(
        total_courses=total,
        pending_courses=pending,
        ready_courses=ready,
        published_courses=published,
        total_clicks=total_clicks,
        clicks_today=clicks_today,
        posts_this_month=posts_month,
    )


# --- Crawler ---
@router.post("/crawler/run")
async def trigger_crawler(background_tasks: BackgroundTasks, _: str = Depends(get_current_admin)):
    background_tasks.add_task(run_crawler)
    return {"message": "Crawler iniciado em background"}


# --- Courses Pending ---
@router.get("/courses/pending", response_model=list[CourseOut])
async def get_pending_courses(_: str = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Course).where(Course.status == "pending").order_by(Course.detected_at.desc())
    )
    return [CourseOut.model_validate(c) for c in result.scalars().all()]


# --- Set Affiliate Link ---
@router.put("/courses/{course_id}/affiliate", response_model=CourseOut)
async def set_affiliate_link(
    course_id: str,
    body: AffiliateLinkRequest,
    _: str = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    course.affiliate_link = body.affiliate_link
    course.status = "manual_link_created"
    course.manual_link_created_at = datetime.utcnow()
    course.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(course)
    return CourseOut.model_validate(course)


# --- Courses Ready to Publish ---
@router.get("/courses/ready", response_model=list[CourseOut])
async def get_ready_courses(_: str = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Course).where(Course.status == "manual_link_created").order_by(Course.manual_link_created_at.desc())
    )
    return [CourseOut.model_validate(c) for c in result.scalars().all()]


# --- Publish Today's Post ---
@router.post("/posts/publish-today", response_model=PostOut)
async def publish_today(_: str = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    # Pegar cursos prontos
    result = await db.execute(select(Course).where(Course.status == "manual_link_created"))
    courses = result.scalars().all()
    if not courses:
        raise HTTPException(status_code=400, detail="Nenhum curso com link de afiliado cadastrado")

    # Criar ou atualizar post do dia
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    today_title = f"Cursos gratuitos da Udemy - {datetime.utcnow().strftime('%d/%m/%Y')}"

    result = await db.execute(select(Post).where(Post.slug == today_str))
    post = result.scalar_one_or_none()

    if not post:
        post = Post(slug=today_str, title=today_title, content_html="")
        db.add(post)
        await db.flush()

    # Cursos já associados ao post
    existing_assoc = await db.execute(
        select(PostCourse.course_id).where(PostCourse.post_id == post.id)
    )
    existing_ids = set(existing_assoc.scalars().all())

    # Adicionar novos cursos
    new_courses = [c for c in courses if c.id not in existing_ids]
    for course in new_courses:
        db.add(PostCourse(post_id=post.id, course_id=course.id))
        course.status = "published"
        course.updated_at = datetime.utcnow()

    # Gerar HTML do post (todos os cursos do post)
    all_course_ids_result = await db.execute(
        select(PostCourse.course_id).where(PostCourse.post_id == post.id)
    )
    all_course_ids = all_course_ids_result.scalars().all()
    # Incluir os novos
    all_ids = set(all_course_ids) | {c.id for c in new_courses}

    all_courses_result = await db.execute(select(Course).where(Course.id.in_(all_ids)))
    all_courses = all_courses_result.scalars().all()

    post.content_html = generate_post_html(all_courses)
    post.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(post)

    return PostOut(
        id=post.id,
        slug=post.slug,
        title=post.title,
        content_html=post.content_html,
        published_at=post.published_at,
        courses=[CourseOut.model_validate(c) for c in all_courses],
    )


def generate_post_html(courses: list[Course]) -> str:
    """Gera HTML do post com os cursos."""
    items_html = ""
    for c in courses:
        price_display = "GRÁTIS" if c.is_free else f"R${c.discount_price:.2f}"
        items_html += f"""
<div class="course-card" style="border:1px solid #eee;border-radius:8px;padding:16px;margin-bottom:16px;">
  <img src="{c.image_url}" alt="{c.title}" style="width:100%;border-radius:4px;margin-bottom:8px;">
  <h3 style="margin:0 0 4px 0;">{c.title}</h3>
  <p style="color:#666;font-size:14px;margin:0 0 4px 0;">{c.instructor}</p>
  <p style="color:#666;font-size:13px;margin:0 0 8px 0;">{c.description[:200]}</p>
  <p><del style="color:#999;">R${c.original_price:.2f}</del> <strong style="color:#16a34a;">{price_display}</strong></p>
  <a href="{c.affiliate_link}" target="_blank" rel="noopener noreferrer"
     style="display:inline-block;background:#7c3aed;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:bold;">
    🎓 Obter curso
  </a>
</div>"""

    return f"<div class='post-courses'>{items_html}</div>"


# --- Logs ---
@router.get("/logs", response_model=list[LogOut])
async def get_logs(
    limit: int = Query(100, le=500),
    _: str = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Log).order_by(Log.created_at.desc()).limit(limit))
    return [LogOut.model_validate(l) for l in result.scalars().all()]


# --- Delete course ---
@router.delete("/courses/{id}")
async def delete_course(id: str, _: str = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).where(Course.id == id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(course)
    await db.commit()
    return {"ok": True}


# --- Clicks ---
@router.get("/clicks", response_model=list[ClickOut])
async def admin_clicks(
    page: int = Query(1, ge=1),
    _: str = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Click).order_by(Click.clicked_at.desc()).offset((page - 1) * 100).limit(100)
    )
    return [ClickOut.model_validate(c) for c in result.scalars().all()]
