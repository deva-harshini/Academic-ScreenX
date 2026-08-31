import re
from pathlib import Path
from typing import Dict, Any, List, Tuple
from pypdf import PdfReader
from app.agents.base import BaseAgent, logger
from app.schemas import ComplianceResult

REQUIRED_SECTIONS = [
    {
        "key": "Introduction",
        "patterns": [r"(?i)\b(1\.?\s*)?introduction\b", r"(?i)\bbackground\b", r"(?i)\bmotivation\b"]
    },
    {
        "key": "Methodology",
        "patterns": [r"(?i)\b(2\.?\s*)?methodology\b", r"(?i)\bproposed method(s)?\b", r"(?i)\bsystem design\b", r"(?i)\bapproach\b", r"(?i)\barchitecture\b"]
    },
    {
        "key": "Results",
        "patterns": [r"(?i)\b(3\.?\s*)?results\b", r"(?i)\bexpected (outcomes|results)\b", r"(?i)\bevaluation\b", r"(?i)\bexperimental setup\b"]
    },
    {
        "key": "Conclusion",
        "patterns": [r"(?i)\b(4\.?\s*)?conclusion\b", r"(?i)\bdiscussion\b", r"(?i)\bfuture work\b", r"(?i)\bsummary\b"]
    }
]

class ComplianceAuditor(BaseAgent):
    """
    Stage 1 Agent:
    Validates structural formatting, word count (250-500 words),
    and presence of mandatory academic sections.
    """
    def __init__(self):
        super().__init__(name="Compliance Auditor", role="Stage 1 Structural & Format Validator")

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        text = ""
        try:
            reader = PdfReader(str(pdf_path))
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            logger.error(f"Error reading PDF {pdf_path}: {e}")
            raise ValueError(f"Failed to read PDF file: {str(e)}")
        
        # Clean up excessive whitespace
        text = re.sub(r'\r\n|\r', '\n', text)
        return text.strip()

    def parse_metadata(self, text: str, fallback_title: str) -> Tuple[str, str]:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        title = fallback_title
        student = "Student Researcher"

        if lines:
            # First non-trivial line often contains title
            for line in lines[:3]:
                if len(line) > 10 and not line.lower().startswith("abstract") and not line.lower().startswith("student:"):
                    title = line
                    break
        
        # Look for explicit author/student labels
        student_match = re.search(r"(?i)(?:student|author|submitted by|applicant):\s*([^\n\r]+)", text)
        if student_match:
            student = student_match.group(1).strip()
        elif len(lines) > 1 and ("student" in lines[1].lower() or "department" in lines[1].lower() or "candidate" in lines[1].lower()):
            student = lines[1].strip()

        return title, student

    def check_sections(self, text: str) -> Tuple[List[str], List[str]]:
        detected = []
        missing = []

        for section in REQUIRED_SECTIONS:
            sec_name = section["key"]
            found = False
            for pattern in section["patterns"]:
                if re.search(pattern, text):
                    found = True
                    break
            if found:
                detected.append(sec_name)
            else:
                missing.append(sec_name)

        return detected, missing

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pdf_path = Path(context.get("pdf_path"))
        fallback_title = context.get("fallback_title", pdf_path.stem.replace("_", " ").title())
        
        extracted_text = self.extract_text_from_pdf(pdf_path)
        title, student_name = self.parse_metadata(extracted_text, fallback_title)
        
        # Count words (alphanumeric tokens)
        words = re.findall(r'\b\w+\b', extracted_text)
        word_count = len(words)
        
        # Check criteria
        is_word_count_valid = (250 <= word_count <= 500)
        detected_sections, missing_sections = self.check_sections(extracted_text)
        
        # Scoring logic (0.0 to 10.0)
        # Word count accounts for 4 points
        if is_word_count_valid:
            wc_score = 4.0
        elif 200 <= word_count < 250 or 500 < word_count <= 550:
            wc_score = 2.5
        elif 100 <= word_count < 200 or 550 < word_count <= 700:
            wc_score = 1.0
        else:
            wc_score = 0.0

        # Each required section accounts for 1.5 points (total 6.0)
        sec_score = len(detected_sections) * 1.5
        compliance_score = round(wc_score + sec_score, 1)
        
        passed = (is_word_count_valid and len(missing_sections) == 0)

        # Generate actionable diagnostic feedback
        feedback_parts = []
        if is_word_count_valid:
            feedback_parts.append(f"✓ Word count is valid ({word_count} words; target: 250-500 words).")
        else:
            if word_count < 250:
                feedback_parts.append(f"✗ Word count too low ({word_count} words). Academic abstracts must contain at least 250 words.")
            else:
                feedback_parts.append(f"✗ Word count exceeded ({word_count} words). Academic abstracts must not exceed 500 words.")

        if not missing_sections:
            feedback_parts.append(f"✓ All mandatory structural sections detected ({', '.join(detected_sections)}).")
        else:
            feedback_parts.append(f"✗ Missing required sections: {', '.join(missing_sections)}.")

        feedback = " ".join(feedback_parts)

        result = ComplianceResult(
            passed=passed,
            word_count=word_count,
            is_word_count_valid=is_word_count_valid,
            detected_sections=detected_sections,
            missing_sections=missing_sections,
            compliance_score=compliance_score,
            feedback=feedback,
            extracted_text=extracted_text,
            title=title,
            student_name=student_name
        )

        return result.model_dump()
