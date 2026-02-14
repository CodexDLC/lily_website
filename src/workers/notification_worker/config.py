from pathlib import Path

from pydantic_settings import BaseSettings


class WorkerSettings(BaseSettings):
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Global Site Settings
    SITE_URL: str = "http://localhost:8000"
    LOGO_URL: str = (
        "https://pinlite.dev/media/storage/a3/65/a365b5fedad7fb5779bc5fcf63f00ebc19ed90808c4010a0fbec7207773ca95e.png"
    )

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent  # lily_website root
    TEMPLATES_DIR: Path = Path(__file__).resolve().parent.parent / "templates"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = WorkerSettings()
