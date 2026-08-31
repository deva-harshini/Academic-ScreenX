import os
import json
import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_

from app.database import get_db, SessionLocal
from app.models import Submission, User, SubmissionStatus
from app.schemas import (
    SubmissionListItem,
    SubmissionDetail,
    DashboardStats,
    PipelineEvaluation
)
from app.auth import get_current_user_optional, get_current_user
from app.config import settings
from app.agents.pipeline import pipeline_engine
from app.agents.base import logger

router = APIRouter(prefix="/api/submissions", tags=["Submissions"])

def process_submission_task(submission_id: int):
    """
    Background worker task: executes the 3-stage autonomous agent pipeline
    and updates the database record with evaluation metrics.
    """
    db = SessionLocal()
    try:
        sub = db.query(Submission).filter(Submission.id == submission_id).first()
        if not sub:
            logger.error(f"Background task could not find submission ID {submission_id}")
            return

        sub.status = SubmissionStatus.PROCESSING.value
        sub.current_stage = "Stage 1: Compliance Auditor"
        db.commit()

        # Run multi-agent pipeline
        eval_result: PipelineEvaluation = pipeline_engine.process_pdf(
            pdf_path=sub.file_path,
            fallback_title=sub.title
        )

        # Update model with Stage 1
        sub.title = eval_result.title
        sub.student_name = eval_result.student_name
        sub.compliance_score = eval_result.compliance.compliance_score
        sub.word_count = eval_result.compliance.word_count
        sub.detected_sections = json.dumps(eval_result.compliance.detected_sections)
        sub.missing_sections = json.dumps(eval_result.compliance.missing_sections)
        sub.compliance_feedback = eval_result.compliance.feedback

        # Update model with Stage 2
        if eval_result.novelty:
            sub.novelty_score = eval_result.novelty.novelty_score
            sub.extracted_methodology = eval_result.novelty.extracted_methodology
            sub.generated_search_queries = json.dumps(eval_result.novelty.search_queries)
            sub.search_matches = json.dumps([m.model_dump() for m in eval_result.novelty.search_matches])
            sub.novelty_verdict = eval_result.novelty.verdict

        # Update model with Stage 3
        if eval_result.critic:
            sub.overall_score = eval_result.critic.overall_score
            sub.dataset_feasibility = eval_result.critic.dataset_feasibility
            sub.dataset_analysis = eval_result.critic.dataset_analysis
            sub.technical_depth_score = eval_result.critic.technical_depth_score
            sub.methodology_rigor_score = eval_result.critic.methodology_rigor_score
            sub.summary = eval_result.critic.summary_review

        sub.status = eval_result.final_status
        sub.current_stage = "Completed"
        sub.processing_time_seconds = eval_result.processing_time_seconds
        sub.error_message = eval_result.error_message
        sub.processed_at = datetime.now(timezone.utc)

        db.commit()
        logger.info(f"Background task finalized for submission #{sub.id} -> Status: {sub.status}")

    except Exception as e:
        logger.error(f"Error in background task for submission {submission_id}: {e}", exc_info=True)
        sub = db.query(Submission).filter(Submission.id == submission_id).first()
        if sub:
            sub.status = SubmissionStatus.FAILED.value
            sub.error_message = str(e)
            sub.current_stage = "Failed"
            db.commit()
    finally:
        db.close()

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_submissions(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Accepts single or batch PDF uploads, validates file type, creates records,
    and enqueues background processing tasks.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    created_submissions = []

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            continue # skip non-pdf files

        # Generate unique filename
        file_ext = Path(file.filename).suffix
        safe_base = "".join(c for c in Path(file.filename).stem if c.isalnum() or c in ("-", "_")).rstrip()
        unique_name = f"{safe_base}_{uuid.uuid4().hex[:8]}{file_ext}"
        save_path = settings.UPLOAD_DIR / unique_name

        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size_kb = round(os.path.getsize(save_path) / 1024, 2)
        initial_title = file.filename.replace(".pdf", "").replace("_", " ").title()

        submission = Submission(
            user_id=current_user.id if current_user else None,
            title=initial_title,
            student_name="Pending Extraction...",
            pdf_filename=file.filename,
            file_path=str(save_path),
            file_size_kb=file_size_kb,
            status=SubmissionStatus.PENDING.value,
            current_stage="Enqueued in Agent Pipeline"
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)

        # Enqueue background processing
        background_tasks.add_task(process_submission_task, submission.id)
        created_submissions.append({
            "id": submission.id,
            "filename": submission.pdf_filename,
            "status": submission.status
        })

    if not created_submissions:
        raise HTTPException(status_code=400, detail="No valid PDF documents were found in the upload request.")

    return {
        "message": f"Successfully queued {len(created_submissions)} proposal(s) for multi-agent evaluation.",
        "submissions": created_submissions
    }

@router.get("/list", response_model=List[SubmissionListItem])
def list_submissions(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None, alias="q"),
    sort_by: str = Query("date_desc", alias="sort"),
    db: Session = Depends(get_db)
):
    query = db.query(Submission)

    if status_filter and status_filter.lower() != "all":
        query = query.filter(Submission.status == status_filter.lower())

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Submission.title.ilike(search_pattern),
                Submission.student_name.ilike(search_pattern),
                Submission.pdf_filename.ilike(search_pattern)
            )
        )

    if sort_by == "score_desc":
        query = query.order_by(desc(Submission.overall_score))
    elif sort_by == "score_asc":
        query = query.order_by(asc(Submission.overall_score))
    elif sort_by == "novelty_desc":
        query = query.order_by(desc(Submission.novelty_score))
    elif sort_by == "date_asc":
        query = query.order_by(asc(Submission.uploaded_at))
    else: # default date_desc
        query = query.order_by(desc(Submission.uploaded_at))

    submissions = query.all()
    return submissions

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total = db.query(Submission).count()
    approved = db.query(Submission).filter(Submission.status == SubmissionStatus.APPROVED.value).count()
    revision = db.query(Submission).filter(Submission.status == SubmissionStatus.REVISION.value).count()
    flagged = db.query(Submission).filter(Submission.status == SubmissionStatus.FLAGGED.value).count()

    approved_pct = round((approved / total * 100), 1) if total > 0 else 0.0
    flagged_pct = round((flagged / total * 100), 1) if total > 0 else 0.0

    # Compute average processing time for completed submissions
    completed = db.query(Submission).filter(Submission.processing_time_seconds > 0).all()
    if completed:
        avg_time = round(sum(s.processing_time_seconds for s in completed) / len(completed), 2)
    else:
        avg_time = 0.0

    return DashboardStats(
        total_uploaded=total,
        approved_count=approved,
        revision_count=revision,
        flagged_count=flagged,
        approved_pct=approved_pct,
        flagged_pct=flagged_pct,
        avg_processing_time=avg_time
    )

@router.get("/{submission_id}/report", response_model=SubmissionDetail)
def get_submission_report(submission_id: int, db: Session = Depends(get_db)):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")

    # Parse JSON fields safely
    def safe_json(val, default):
        if not val: return default
        try: return json.loads(val)
        except Exception: return default

    return SubmissionDetail(
        id=sub.id,
        title=sub.title,
        student_name=sub.student_name,
        pdf_filename=sub.pdf_filename,
        file_size_kb=sub.file_size_kb,
        status=sub.status,
        current_stage=sub.current_stage,
        compliance_score=sub.compliance_score,
        novelty_score=sub.novelty_score,
        overall_score=sub.overall_score,
        dataset_feasibility=sub.dataset_feasibility,
        summary=sub.summary,
        processing_time_seconds=sub.processing_time_seconds,
        uploaded_at=sub.uploaded_at,
        processed_at=sub.processed_at,
        word_count=sub.word_count,
        detected_sections=safe_json(sub.detected_sections, []),
        missing_sections=safe_json(sub.missing_sections, []),
        compliance_feedback=sub.compliance_feedback,
        extracted_methodology=sub.extracted_methodology,
        generated_search_queries=safe_json(sub.generated_search_queries, []),
        search_matches=safe_json(sub.search_matches, []),
        novelty_verdict=sub.novelty_verdict,
        dataset_analysis=sub.dataset_analysis,
        technical_depth_score=sub.technical_depth_score,
        methodology_rigor_score=sub.methodology_rigor_score,
        error_message=sub.error_message
    )

@router.delete("/{submission_id}")
def delete_submission(submission_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")

    # Remove physical file if exists
    try:
        if os.path.exists(sub.file_path):
            os.remove(sub.file_path)
    except Exception as e:
        logger.warning(f"Could not delete physical file: {e}")

    db.delete(sub)
    db.commit()
    return {"message": "Submission successfully removed."}
