from datetime import datetime
from pydantic import BaseModel


# --- Course ---
class CourseOut(BaseModel):
    id: str
    title: str
    slug: str
    udemy_url: str
    description: str
    instructor: str
    image_url: str
    category: str
    language: str
    rating: float
    students_count: int
    num_reviews: int
    original_price: float
    discount_price: float
    discount_percent: int
    coupon_code: str
    affiliate_link: str
    is_free: bool
    status: str
    detected_at: datetime
    manual_link_created_at: datetime | None
    category_id: str | None = None
    promoted_at: datetime | None = None

    class Config:
        from_attributes = True


class CoursePaginated(BaseModel):
    items: list[CourseOut]
    total: int
    page: int
    pages: int


class AffiliateLinkRequest(BaseModel):
    affiliate_link: str = ""


# --- Post ---
class PostOut(BaseModel):
    id: str
    slug: str
    title: str
    content_html: str
    published_at: datetime
    courses: list[CourseOut] = []

    class Config:
        from_attributes = True


class PostSummary(BaseModel):
    id: str
    slug: str
    title: str
    published_at: datetime
    course_count: int = 0

    class Config:
        from_attributes = True


# --- Log ---
class LogOut(BaseModel):
    id: str
    agent_name: str
    level: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Auth ---
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Dashboard ---
class DashboardStats(BaseModel):
    total_courses: int
    pending_courses: int
    ready_courses: int
    published_courses: int
    total_clicks: int
    clicks_today: int
    posts_this_month: int


# --- Click ---
class ClickOut(BaseModel):
    id: str
    course_id: str
    ip_address: str
    clicked_at: datetime

    class Config:
        from_attributes = True


# --- Category ---
class CategoryCreate(BaseModel):
    name: str
    description: str = ""
    telegram_channels: list[str] = []
    discord_webhooks: list[str] = []
    subreddits: list[str] = []
    twitter_keywords: list[str] = []


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    telegram_channels: list[str] | None = None
    discord_webhooks: list[str] | None = None
    subreddits: list[str] | None = None
    twitter_keywords: list[str] | None = None
    is_active: bool | None = None


class CategoryOut(BaseModel):
    id: str
    name: str
    description: str
    telegram_channels: list[str]
    discord_webhooks: list[str]
    subreddits: list[str]
    twitter_keywords: list[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Promotion Log ---
class PromotionLogOut(BaseModel):
    id: str
    course_id: str
    platform: str
    target: str
    status: str
    error_message: str
    sent_at: datetime

    class Config:
        from_attributes = True


# --- Course Category ---
class CourseCategoryRequest(BaseModel):
    category_id: str | None = None
