import pytest
import tempfile
from pathlib import Path
from services.ai_evaluator import evaluate_document, _load_document_chunks, DEFAULT_ACADEMIC_CRITERIA
from app.services.ai_evaluator import evaluate_document as app_evaluate_document

SAMPLE_PDF_INNOVATIVE = Path(__file__).resolve().parent.parent / "sample_pdfs" / "03_innovative_idea.pdf"
SAMPLE_PDF_INVALID = Path(__file__).resolve().parent.parent / "sample_pdfs" / "01_invalid_format.pdf"

def test_evaluate_document_pdf_innovative():
    """Test RAG evaluation on a well-structured academic proposal PDF"""
    assert SAMPLE_PDF_INNOVATIVE.exists(), f"Sample PDF missing: {SAMPLE_PDF_INNOVATIVE}"
    
    result = evaluate_document(str(SAMPLE_PDF_INNOVATIVE))
    
    assert isinstance(result, dict)
    assert "Match Status" in result
    assert result["Match Status"] in ["Qualified", "Not Qualified", "Needs Review"]
    assert "Key Evidence Found" in result
    assert isinstance(result["Key Evidence Found"], list)
    assert "Missing Requirements" in result
    assert isinstance(result["Missing Requirements"], list)
    assert "metadata" in result

def test_evaluate_document_pdf_invalid():
    """Test RAG evaluation on an incomplete proposal PDF"""
    assert SAMPLE_PDF_INVALID.exists(), f"Sample PDF missing: {SAMPLE_PDF_INVALID}"
    
    result = evaluate_document(str(SAMPLE_PDF_INVALID))
    
    assert isinstance(result, dict)
    assert "Match Status" in result
    assert result["Match Status"] in ["Qualified", "Not Qualified", "Needs Review"]
    assert len(result["Missing Requirements"]) > 0

def test_evaluate_document_txt():
    """Test RAG evaluation on a plain TXT proposal document"""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("""
Title: Edge Computing for Autonomous Drone Navigation
Author: Alex Turing

1. Introduction
Autonomous aerial navigation under GPS-denied environments poses severe latency constraints.

2. Methodology
We propose a lightweight vision-transformer pipeline deployed directly on onboard neuromorphic chips.

3. Dataset and Benchmarks
Evaluated on the Mid-Air UAV Benchmark Dataset across 1,200 flight trajectories.

4. Results and Conclusion
Our system achieves 98.4% obstacle avoidance accuracy while consuming under 2.5 Watts.
        """)
        txt_path = f.name

    try:
        result = evaluate_document(txt_path)
        assert isinstance(result, dict)
        assert result["Match Status"] == "Qualified"
        assert len(result["Key Evidence Found"]) > 0
    finally:
        Path(txt_path).unlink(missing_ok=True)

def test_app_services_alias():
    """Test that app.services.ai_evaluator and services.ai_evaluator both export evaluate_document"""
    assert evaluate_document is not None
    assert app_evaluate_document is not None

def test_chunking_settings():
    """Test chunking parameters (chunk_size=500, chunk_overlap=50)"""
    assert SAMPLE_PDF_INNOVATIVE.exists()
    chunks = _load_document_chunks(str(SAMPLE_PDF_INNOVATIVE), chunk_size=500, chunk_overlap=50)
    assert len(chunks) > 0
    for chunk in chunks:
        assert len(chunk.page_content) <= 600 # accounting for word boundaries
