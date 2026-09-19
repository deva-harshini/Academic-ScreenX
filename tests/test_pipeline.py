import os
import re
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine, SessionLocal
from app.auth import ensure_default_faculty_user
from app.config import settings
from app.agents.pipeline import pipeline_engine
from app.agents.compliance import ComplianceAuditor
from app.agents.novelty import NoveltyAssessor
from app.agents.critic import TechnicalCritic

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_pdfs"

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_default_faculty_user(db)
    finally:
        db.close()
    yield

def test_agent1_compliance_auditor():
    auditor = ComplianceAuditor()
    
    # 1. Invalid PDF: word count too low & missing sections
    res1 = auditor.evaluate({"pdf_path": str(SAMPLE_DIR / "01_invalid_format.pdf")})
    assert res1["passed"] is False
    assert res1["word_count"] < 250
    assert "Methodology" in res1["missing_sections"]
    assert "Results" in res1["missing_sections"]
    assert res1["compliance_score"] < 6.0

    # 2. Compliant PDF
    res3 = auditor.evaluate({"pdf_path": str(SAMPLE_DIR / "03_innovative_idea.pdf")})
    assert res3["passed"] is True
    assert 250 <= res3["word_count"] <= 500
    assert len(res3["missing_sections"]) == 0
    assert res3["compliance_score"] >= 8.0

def test_agent2_novelty_assessor():
    assessor = NoveltyAssessor()
    
    # Check copied MNIST CNN
    context_copied = {
        "compliance": {
            "title": "Handwritten Digit Recognition using Convolutional Neural Networks on MNIST",
            "extracted_text": "We evaluate a sequential Convolutional Neural Network on the canonical MNIST dataset comprising 60,000 images."
        }
    }
    res_copied = assessor.evaluate(context_copied)
    assert res_copied["novelty_score"] < 4.5
    assert res_copied["is_novel"] is False
    assert len(res_copied["search_matches"]) > 0

    # Check novel HDC edge proposal
    context_novel = {
        "compliance": {
            "title": "Neuromorphic Hyperdimensional Computing on Edge MEMS",
            "extracted_text": "Spike-driven Hyperdimensional Computing architecture mapping continuous multi-channel ECG signals into 8192-bit holographic vectors on FD-SOI."
        }
    }
    res_novel = assessor.evaluate(context_novel)
    assert res_novel["novelty_score"] >= 7.0
    assert res_novel["is_novel"] is True

def test_agent3_technical_critic():
    critic = TechnicalCritic()
    context = {
        "compliance": {
            "passed": True,
            "compliance_score": 9.0,
            "word_count": 350,
            "is_word_count_valid": True,
            "detected_sections": ["Introduction", "Methodology", "Results", "Conclusion"],
            "missing_sections": [],
            "extracted_text": "Evaluated against PhysioNet MIT-BIH dataset with 97.4% accuracy.",
            "title": "Neuromorphic Edge ECG",
            "student_name": "Priya Nair"
        },
        "novelty": {
            "novelty_score": 8.5,
            "is_novel": True,
            "extracted_methodology": "Couples an asynchronous event-based delta modulator with a ternary HDC encoder",
            "verdict": "High Novelty"
        }
    }
    res_critic = critic.evaluate(context)
    assert res_critic["overall_score"] >= 7.0
    assert res_critic["recommendation"] == "Approved for Faculty"
    assert res_critic["final_status"] == "approved"
    assert res_critic["dataset_feasibility"] == "High"
    
    # Verify exactly 3 sentences
    summary = res_critic["summary_review"].strip()
    sentences = [s.strip() for s in re.split(r'\.\s+', summary.rstrip('.')) if s.strip()]
    assert len(sentences) == 3

def test_full_multi_agent_pipeline():
    # 1. Invalid format -> Needs Revision
    eval1 = pipeline_engine.process_pdf(str(SAMPLE_DIR / "01_invalid_format.pdf"))
    assert eval1.final_status == "revision"
    assert eval1.compliance.passed is False

    # 2. Copied Idea -> Flagged for Low Novelty
    eval2 = pipeline_engine.process_pdf(str(SAMPLE_DIR / "02_copied_idea.pdf"))
    assert eval2.final_status == "flagged"
    assert eval2.novelty.is_novel is False

    # 3. Innovative Idea -> Approved for Faculty
    eval3 = pipeline_engine.process_pdf(str(SAMPLE_DIR / "03_innovative_idea.pdf"))
    assert eval3.final_status == "approved"
    assert eval3.critic.overall_score >= 7.0

def test_api_endpoints():
    with TestClient(app) as client:
        # Auth Login
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "faculty@university.edu", "password": "ASX_Faculty#2026!Pass"}
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Upload single sample
        pdf_path = SAMPLE_DIR / "03_innovative_idea.pdf"
        with open(pdf_path, "rb") as f:
            upload_resp = client.post(
                "/api/submissions/upload",
                files={"files": ("03_innovative_idea.pdf", f, "application/pdf")},
                headers=headers
            )
        assert upload_resp.status_code == 202
        sub_id = upload_resp.json()["submissions"][0]["id"]

        # List submissions
        list_resp = client.get("/api/submissions/list", headers=headers)
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert len(items) >= 1

        # Stats endpoint
        stats_resp = client.get("/api/submissions/stats")
        assert stats_resp.status_code == 200
        stats = stats_resp.json()
        assert "total_uploaded" in stats
        assert "approved_pct" in stats
