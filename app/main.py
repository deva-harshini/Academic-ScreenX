import urllib.parse
import sys
import os
from pathlib import Path

# Ensure project root is in sys.path for direct module import compatibility across local & Vercel
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base, SessionLocal, init_db
from app.routes import auth_routes, submission_routes, web_routes
from app.agents.base import logger

BASE_DIR = Path(__file__).resolve().parent.parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure DB tables exist and seed demo user
    logger.info("Initializing Academic-ScreenX Database...")
    init_db()
    yield
    # Shutdown
    logger.info("Academic-ScreenX shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Autonomous Multi-Agent Paper Screening Platform for University Faculty",
    lifespan=lifespan
)

# Vercel Serverless ASGI Path Normalizer Middleware
@app.middleware("http")
async def vercel_path_normalizer(request: Request, call_next):
    """
    Normalizes request paths when running on Vercel Serverless.
    Vercel provides the rewritten client path in 'x-now-route-matches' (e.g. 1=demo%2Fload-samples),
    'x-invoke-path', 'x-original-url', or raw ASGI scope path.
    """
    # 1. Check Vercel rewrite capture groups in 'x-now-route-matches'
    route_matches = request.headers.get("x-now-route-matches")
    extracted_path = None
    if route_matches:
        try:
            parsed = urllib.parse.parse_qs(route_matches)
            for k in ["1", "path", "match", "0"]:
                if k in parsed and parsed[k]:
                    val = parsed[k][0]
                    extracted_path = "/" + val.lstrip("/")
                    break
        except Exception:
            pass

    # 2. Check direct invoked path headers
    if not extracted_path:
        for h in ["x-invoke-path", "x-original-url", "x-forwarded-uri", "x-vercel-path", "x-rewrite-url"]:
            val = request.headers.get(h)
            if val:
                clean = val.split("?")[0].strip()
                if clean and clean not in ("/api/index.py", "/fastapi", "/api/index"):
                    extracted_path = clean
                    break

    # 3. Check ASGI scope path prefixes
    if not extracted_path:
        scope_path = request.scope.get("path", "")
        for prefix in ["/api/index.py", "/api/index", "/fastapi"]:
            if scope_path.startswith(prefix):
                norm = scope_path[len(prefix):]
                extracted_path = norm if norm else "/"
                break
        if not extracted_path:
            extracted_path = scope_path or "/"

    request.scope["path"] = extracted_path
    return await call_next(request)

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

# Expose handler for Vercel Serverless / AWS Lambda execution
handler = app
