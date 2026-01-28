"""
Application configuration management.
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

# Get the project root directory (where app/ folder is located)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Control Mapping Application"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = f"sqlite+aiosqlite:///{PROJECT_ROOT}/storage/jobs.db"

    # File storage paths (resolved to absolute paths)
    upload_dir: Path = PROJECT_ROOT / "storage" / "uploads"
    output_dir: Path = PROJECT_ROOT / "storage" / "outputs"
    providers_dir: Path = PROJECT_ROOT / "providers"
    prompts_dir: Path = PROJECT_ROOT / "prompts"

    # Claude Code settings
    claude_timeout: int = 600  # seconds
    claude_allowed_tools: str = "Read,Glob"

    # File upload limits
    max_upload_size: int = 10 * 1024 * 1024  # 10MB

    # Supported file types
    allowed_extensions: set = {".pdf", ".csv", ".xlsx", ".xls", ".json", ".txt"}

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings
