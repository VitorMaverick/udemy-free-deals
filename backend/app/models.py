import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    udemy_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
    udemy_url: Mapped[str] = mapped_column(String(2000), default="", index=True)
    title: Mapped[str] = mapped_column(String(500))
    slug: Mapped[str] = mapped_column(String(500), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    instructor: Mapped[str] = mapped_column(String(200), default="")
    image_url: Mapped[str] = mapped_column(String(1000), default="")
    category: Mapped[str] = mapped_column(String(100), default="", index=True)
    language: Mapped[str] = mapped_column(String(50), default="")
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    students_count: Mapped[int] = mapped_column(Integer, default=0)
    num_reviews: Mapped[int] = mapped_column(Integer, default=0)
    original_price: Mapped[float] = mapped_column(Float, default=0.0)
    discount_price: Mapped[float] = mapped_column(Float, default=0.0)
    discount_percent: Mapped[int] = mapped_column(Integer, default=100)
    coupon_code: Mapped[str] = mapped_column(String(255), default="")
    affiliate_link: Mapped[str] = mapped_column(String(500), default="")
    is_free: Mapped[bool] = mapped_column(Boolean, default=True)
    # Status: pending | manual_link_created | published | expired
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    manual_link_created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    slug: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # YYYY-MM-DD
    title: Mapped[str] = mapped_column(String(300))
    content_html: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PostCourse(Base):
    """Associação entre post e cursos incluídos nele."""
    __tablename__ = "post_courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    post_id: Mapped[str] = mapped_column(String(36), ForeignKey("posts.id"))
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id"))


class Log(Base):
    __tablename__ = "logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    agent_name: Mapped[str] = mapped_column(String(50), default="crawler")
    level: Mapped[str] = mapped_column(String(10), default="INFO")
    message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Click(Base):
    __tablename__ = "clicks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id"))
    ip_address: Mapped[str] = mapped_column(String(45), default="")
    user_agent: Mapped[str] = mapped_column(String(500), default="")
    referer: Mapped[str] = mapped_column(String(1000), default="")
    clicked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
