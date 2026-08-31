from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class UserRole(str, enum.Enum):
    FACULTY = "faculty"
    STUDENT = "student"

class SubmissionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"          # Approved for Faculty
    REVISION = "revision"          # Needs Revision (Format/Word count/Missing sections)
    FLAGGED = "flagged"            # Flagged for Low Novelty
    FAILED = "failed"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.FACULTY.value, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    submissions = relationship("Submission", back_populates="user", cascade="all, delete-orphan")

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    title = Column(String(500), nullable=False, default="Untitled Abstract")
    student_name = Column(String(255), nullable=True, default="Anonymous Applicant")
    pdf_filename = Column(String(255), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size_kb = Column(Float, default=0.0)
    
    status = Column(String(50), default=SubmissionStatus.PENDING.value, index=True)
    current_stage = Column(String(100), default="Queued")
    
    # Stage 1: Compliance
    compliance_score = Column(Float, default=0.0)
    word_count = Column(Integer, default=0)
    detected_sections = Column(Text, default="[]")  # JSON list
    missing_sections = Column(Text, default="[]")   # JSON list
    compliance_feedback = Column(Text, nullable=True)
    
    # Stage 2: Novelty
    novelty_score = Column(Float, default=0.0)     # 0.0 - 10.0 (10 = highly novel)
    extracted_methodology = Column(Text, nullable=True)
    generated_search_queries = Column(Text, default="[]") # JSON list
    search_matches = Column(Text, default="[]")    # JSON list of detected similar papers/links
    novelty_verdict = Column(String(255), nullable=True)
    
    # Stage 3: Technical Critic
    overall_score = Column(Float, default=0.0)     # S ∈ [1, 10]
    dataset_feasibility = Column(String(50), nullable=True) # High / Moderate / Low / Infeasible
    dataset_analysis = Column(Text, nullable=True)
    technical_depth_score = Column(Float, default=0.0)
    methodology_rigor_score = Column(Float, default=0.0)
    summary = Column(Text, nullable=True)          # 3-sentence summary review
    
    # Execution metrics & audit
    error_message = Column(Text, nullable=True)
    processing_time_seconds = Column(Float, default=0.0)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    processed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="submissions")
