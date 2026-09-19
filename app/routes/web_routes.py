from pathlib import Path
from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import shutil
import uuid
import os

from app.database import get_db
from app.models import Submission, User, SubmissionStatus
from app.auth import get_current_user_optional
from app.config import settings
from app.routes.submission_routes import process_submission_task

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(include_in_schema=False)

def _render_dashboard(request: Request, user: User, db: Session):
    """Helper to render dashboard template with context"""
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": user or {"name": "Dr. Eleanor Vance", "role": "faculty", "email": "faculty@university.edu"},
            "app_name": settings.APP_NAME,
            "app_version": settings.APP_VERSION,
            "use_mock_llm": settings.USE_MOCK_LLM
        }
    )

@router.get("/", response_class=HTMLResponse)
def index_view(request: Request, user: User = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    """Direct root path rendering the main faculty dashboard without redirects."""
    return _render_dashboard(request, user, db)

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, user: User = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    """Render main faculty dashboard."""
    return _render_dashboard(request, user, db)

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user: User = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request=request, name="login.html", context={"app_name": settings.APP_NAME})

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, user: User = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request=request, name="register.html", context={"app_name": settings.APP_NAME})

@router.get("/report/{submission_id}", response_class=HTMLResponse)
def report_page(submission_id: int, request: Request, user: User = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return templates.TemplateResponse(
        request=request,
        name="report.html",
        context={
            "user": user,
            "sub": sub,
            "app_name": settings.APP_NAME
        }
    )

@router.post("/demo/load-samples")
def load_sample_proposals(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    1-Click Demo Seed: Loads the 3 realistic sample PDFs from /sample_pdfs
    and submits them to the multi-agent screening pipeline.
    """
    sample_files = [
        "01_invalid_format.pdf",
        "02_copied_idea.pdf",
        "03_innovative_idea.pdf"
    ]

    try:
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    
    queued = []
    for s_name in sample_files:
        # Search possible sample locations
        src = settings.SAMPLE_DIR / s_name
        if not src.exists():
            # Try alternate paths
            alt = BASE_DIR / "sample_pdfs" / s_name
            if alt.exists():
                src = alt
            else:
                continue

        dest_name = f"demo_{uuid.uuid4().hex[:6]}_{s_name}"
        dest_path = settings.UPLOAD_DIR / dest_name
        shutil.copyfile(src, dest_path)

        file_size_kb = round(os.path.getsize(dest_path) / 1024, 2)
        initial_title = s_name.replace(".pdf", "").replace("_", " ").title()

        submission = Submission(
            title=initial_title,
            student_name="Pending Extraction...",
            pdf_filename=s_name,
            file_path=str(dest_path),
            file_size_kb=file_size_kb,
            status=SubmissionStatus.PENDING.value,
            current_stage="Enqueued in Agent Pipeline"
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)

        background_tasks.add_task(process_submission_task, submission.id)
        queued.append(submission.id)

    if not queued:
        # If files were not found on disk, dynamically generate them
        try:
            from tests.generate_samples import generate_all_samples
            generate_all_samples()
            for s_name in sample_files:
                src = settings.SAMPLE_DIR / s_name
                if src.exists():
                    dest_name = f"demo_{uuid.uuid4().hex[:6]}_{s_name}"
                    dest_path = settings.UPLOAD_DIR / dest_name
                    shutil.copyfile(src, dest_path)
                    file_size_kb = round(os.path.getsize(dest_path) / 1024, 2)
                    initial_title = s_name.replace(".pdf", "").replace("_", " ").title()
                    submission = Submission(
                        title=initial_title,
                        student_name="Pending Extraction...",
                        pdf_filename=s_name,
                        file_path=str(dest_path),
                        file_size_kb=file_size_kb,
                        status=SubmissionStatus.PENDING.value,
                        current_stage="Enqueued in Agent Pipeline"
                    )
                    db.add(submission)
                    db.commit()
                    db.refresh(submission)
                    background_tasks.add_task(process_submission_task, submission.id)
                    queued.append(submission.id)
        except Exception:
            pass

    return {
        "message": f"Successfully queued {len(queued)} sample proposal(s) for multi-agent evaluation.",
        "ids": queued
    }

@router.api_route("/logout", methods=["GET", "POST"])
def logout_view():
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie("access_token")
    return resp
