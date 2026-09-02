import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

def is_serverless_or_readonly() -> bool:
    """
    Robustly detect if the application is running in a serverless or read-only environment
    such as Vercel Serverless Functions, AWS Lambda, or a read-only container.
    """
    # 1. Check explicit Vercel environment flags
    if os.getenv("VERCEL") in ("1", "true", "True"):
        return True
    if os.getenv("VERCEL_ENV") or os.getenv("VERCEL_REGION") or os.getenv("NOW_REGION"):
        return True
        
    # 2. Check AWS Lambda / Serverless container markers
    if os.getenv("LAMBDA_TASK_ROOT") or os.getenv("AWS_EXECUTION_ENV") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return True
        
    # 3. Check if running inside Vercel's standard /var/task deployment path
    if str(BASE_DIR).startswith("/var/task") or str(Path.cwd()).startswith("/var/task"):
        return True
        
    # 4. Active write permission check on BASE_DIR
    try:
        test_file = BASE_DIR / ".write_test"
        test_file.touch()
        test_file.unlink()
        return False
    except (OSError, PermissionError):
        return True

IS_VERCEL = is_serverless_or_readonly()

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
