import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

# Detect serverless environment (e.g. Vercel or AWS Lambda) where root filesystem is read-only
IS_VERCEL = os.getenv("VERCEL") == "1" or "AWS_LAMBDA_FUNCTION_NAME" in os.environ

class Settings(BaseSettings):
    APP_NAME: str = "Academic-ScreenX"
    APP_VERSION: str = "1.0.0"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "academic-screenx-super-secure-secret-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    
    # Database: Use /tmp on Vercel/serverless environments where root filesystem is read-only
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:////tmp/academic_screenx.db" if IS_VERCEL else f"sqlite:///{BASE_DIR}/academic_screenx.db"
    )
    
    # Storage: Use /tmp on Vercel for temporary file parsing during function invocations
    UPLOAD_DIR: Path = Path("/tmp/uploads") if IS_VERCEL else (BASE_DIR / "uploads")
    SAMPLE_DIR: Path = BASE_DIR / "sample_pdfs"
    
    # Mock / External APIs
    USE_MOCK_LLM: bool = os.getenv("USE_MOCK_LLM", "True").lower() in ("true", "1", "yes")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()

# Ensure storage directories exist without crashing on read-only filesystems
try:
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

try:
    settings.SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass
