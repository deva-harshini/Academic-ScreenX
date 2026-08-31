from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime

# --- Auth Schemas ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: Optional[str] = None
    role: str = "faculty"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

# --- Agent 1: Compliance Auditor ---
class ComplianceResult(BaseModel):
    passed: bool
    word_count: int
    is_word_count_valid: bool  # 250 - 500 words
    detected_sections: List[str]
    missing_sections: List[str]
    compliance_score: float    # 0.0 - 10.0
    feedback: str
    extracted_text: str
    title: str
    student_name: Optional[str] = None

# --- Agent 2: Novelty Assessor ---
class SearchMatch(BaseModel):
    title: str
    snippet: str
    url: Optional[str] = None
    similarity_level: str # 'High', 'Moderate', 'Low'
    source_type: str     # 'Literature' | 'Preprint' | 'GitHub' | 'Benchmark'

class NoveltyResult(BaseModel):
    novelty_score: float # 0.0 - 10.0 (10 = highly novel, < 4.0 = high duplicate risk)
    is_novel: bool
    extracted_methodology: str
    search_queries: List[str]
    search_matches: List[SearchMatch]
    verdict: str
    novelty_explanation: str

# --- Agent 3: Technical Critic ---
class CriticResult(BaseModel):
    overall_score: float          # S ∈ [1, 10]
    technical_depth_score: float   # 1 - 10
    methodology_rigor_score: float # 1 - 10
    dataset_feasibility: str      # 'High', 'Moderate', 'Low', 'Infeasible'
    dataset_analysis: str
    summary_review: str           # Exactly 3 sentences
    strengths: List[str]
    weaknesses: List[str]
    recommendation: str           # 'Approved for Faculty', 'Needs Revision', 'Flagged for Low Novelty'

# --- Multi-Agent Orchestrated Pipeline Output ---
class PipelineEvaluation(BaseModel):
    title: str
    student_name: str
    final_status: str # 'approved' | 'revision' | 'flagged' | 'failed'
    compliance: ComplianceResult
    novelty: Optional[NoveltyResult] = None
    critic: Optional[CriticResult] = None
    processing_time_seconds: float
    error_message: Optional[str] = None

# --- Submission API Schemas ---
class SubmissionListItem(BaseModel):
    id: int
    title: str
    student_name: Optional[str]
    pdf_filename: str
    file_size_kb: float
    status: str
    current_stage: str
    compliance_score: float
    novelty_score: float
    overall_score: float
    dataset_feasibility: Optional[str]
    summary: Optional[str]
    processing_time_seconds: float
    uploaded_at: datetime
    processed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class SubmissionDetail(SubmissionListItem):
    word_count: int
    detected_sections: List[str] = []
    missing_sections: List[str] = []
    compliance_feedback: Optional[str]
    extracted_methodology: Optional[str]
    generated_search_queries: List[str] = []
    search_matches: List[Dict[str, Any]] = []
    novelty_verdict: Optional[str]
    dataset_analysis: Optional[str]
    technical_depth_score: float
    methodology_rigor_score: float
    error_message: Optional[str]

class DashboardStats(BaseModel):
    total_uploaded: int
    approved_count: int
    revision_count: int
    flagged_count: int
    approved_pct: float
    flagged_pct: float
    avg_processing_time: float
