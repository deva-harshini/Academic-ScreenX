"""
Services module alias routing to app.services.ai_evaluator.
"""
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.ai_evaluator import (
    evaluate_document,
    DEFAULT_ACADEMIC_CRITERIA,
    _load_document_chunks,
    _mock_heuristic_evaluation
)

__all__ = [
    "evaluate_document",
    "DEFAULT_ACADEMIC_CRITERIA",
    "_load_document_chunks",
    "_mock_heuristic_evaluation"
]

if __name__ == "__main__":
    import json
    test_file = sys.argv[1] if len(sys.argv) > 1 else "sample_pdfs/proposal_approved_1.pdf"
    res = evaluate_document(test_file)
    print(json.dumps(res, indent=2))
