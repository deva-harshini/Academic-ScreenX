from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.auth import ensure_default_faculty_user
from app.routes import auth_routes, submission_routes, web_routes
from app.agents.base import logger

BASE_DIR = Path(__file__).resolve().parent.parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure DB tables exist and seed demo user
    logger.info("Initializing Academic-ScreenX Database...")
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            ensure_default_faculty_user(db)
            logger.info("Default Faculty Account verified: faculty@university.edu / admin123")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error during database initialization: {e}", exc_info=True)
        
    yield
    # Shutdown
    logger.info("Academic-ScreenX shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Autonomous Multi-Agent Paper Screening Platform for University Faculty",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files safely
static_dir = BASE_DIR / "app" / "static"
try:
    static_dir.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Register Routers
app.include_router(auth_routes.router)
app.include_router(submission_routes.router)
app.include_router(web_routes.router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled error: {exc}", exc_info=True)
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred while processing the request."}
        )
    raise exc
