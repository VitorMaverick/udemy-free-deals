from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./dev.db"
    secret_key: str = "change-me-in-production"
    admin_username: str = "admin"
    admin_password: str = "admin123"
    affiliate_tag: str = ""
    crawler_interval_hours: int = 6
    cors_origins: str = "http://localhost:5173"
    access_token_expire_minutes: int = 60 * 24

    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Converter postgresql:// para postgresql+asyncpg:// automaticamente
        if self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)


settings = Settings()
