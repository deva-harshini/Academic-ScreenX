import time
from pathlib import Path
from typing import Dict, Any, Optional
from app.agents.compliance import ComplianceAuditor
from app.agents.novelty import NoveltyAssessor
from app.agents.critic import TechnicalCritic
from app.agents.base import logger
from app.schemas import PipelineEvaluation, ComplianceResult, NoveltyResult, CriticResult
from app.services.ai_evaluator import evaluate_document

class MultiAgentPipeline:
    """
    Orchestrates the Autonomous Paper Screening Pipeline:
    Stage 1: Compliance Auditor (Structure, Word Count 250-500, Mandatory Sections)
    Stage 2: Novelty Assessor (Methodology Extraction & Web Duplicate Detection)
    Stage 3: Technical Critic (1-10 Scoring, Dataset Feasibility, 3-Sentence Summary)
    Layer 4: AI RAG Document Evaluator (LangChain Vector Indexing & Criteria Retrieval)
    """
    def __init__(self):
        self.stage1_compliance = ComplianceAuditor()
        self.stage2_novelty = NoveltyAssessor()
        self.stage3_critic = TechnicalCritic()

    def process_pdf(self, pdf_path: str, fallback_title: Optional[str] = None) -> PipelineEvaluation:
        start_time = time.time()
        path_obj = Path(pdf_path)
        logger.info(f"Starting Multi-Agent & RAG Evaluation for: {path_obj.name}")

        try:
            # Stage 1: Compliance Auditor
            context: Dict[str, Any] = {
                "pdf_path": str(path_obj),
                "fallback_title": fallback_title or path_obj.stem.replace("_", " ").title()
            }
            logger.info("Executing Stage 1: Compliance Auditor...")
            stage1_out = self.stage1_compliance.evaluate(context)
            context["compliance"] = stage1_out

            # Stage 2: Novelty Assessor
            logger.info("Executing Stage 2: Novelty Assessor...")
            stage2_out = self.stage2_novelty.evaluate(context)
            context["novelty"] = stage2_out

            # Stage 3: Technical Critic
            logger.info("Executing Stage 3: Technical Critic...")
            stage3_out = self.stage3_critic.evaluate(context)
            context["critic"] = stage3_out

            # Layer 4: AI RAG Document Evaluator
            logger.info("Executing AI RAG Document Evaluation Layer...")
            try:
                rag_out = evaluate_document(str(path_obj))
            except Exception as rag_err:
                logger.warning(f"RAG evaluation encountered warning: {rag_err}")
                rag_out = {
                    "Match Status": "Needs Review",
                    "Key Evidence Found": [],
                    "Missing Requirements": [str(rag_err)]
                }

            elapsed_time = round(time.time() - start_time, 2)
            final_status = stage3_out.get("final_status", "revision")

            evaluation = PipelineEvaluation(
                title=stage1_out["title"],
                student_name=stage1_out["student_name"] or "Anonymous Applicant",
                final_status=final_status,
                compliance=ComplianceResult(**stage1_out),
                novelty=NoveltyResult(**stage2_out),
                critic=CriticResult(**stage3_out),
                rag_evaluation=rag_out,
                processing_time_seconds=elapsed_time,
                error_message=None
            )

            logger.info(f"Evaluation complete for '{evaluation.title}' -> Status: {final_status} in {elapsed_time}s")
            return evaluation

        except Exception as e:
            elapsed_time = round(time.time() - start_time, 2)
            logger.error(f"Pipeline error for {pdf_path}: {e}", exc_info=True)
            
            # Create a graceful fallback response with failed status
            fallback_compliance = ComplianceResult(
                passed=False,
                word_count=0,
                is_word_count_valid=False,
                detected_sections=[],
                missing_sections=["Introduction", "Methodology", "Results", "Conclusion"],
                compliance_score=0.0,
                feedback=f"Processing failed: {str(e)}",
                extracted_text="",
                title=path_obj.stem.replace("_", " ").title(),
                student_name="Unknown"
            )

            return PipelineEvaluation(
                title=fallback_compliance.title,
                student_name="Unknown",
                final_status="failed",
                compliance=fallback_compliance,
                novelty=None,
                critic=None,
                rag_evaluation=None,
                processing_time_seconds=elapsed_time,
                error_message=str(e)
            )

# Singleton pipeline instance

    def run_pipeline(self, title: str, extracted_text: str, student_name: str = "Student Researcher") -> Dict[str, Any]:
        import re
        start_time = time.time()
        
        # Build stage 1 context
        words = re.findall(r'\b\w+\b', extracted_text)
        word_count = len(words)
        is_word_count_valid = (250 <= word_count <= 500)
        detected_sections, missing_sections = self.stage1_compliance.check_sections(extracted_text)
        
        # Word count scoring
        if is_word_count_valid:
            wc_score = 4.0
        elif 200 <= word_count < 250 or 500 < word_count <= 550:
            wc_score = 2.5
        elif 100 <= word_count < 200 or 550 < word_count <= 700:
            wc_score = 1.0
        else:
            wc_score = 0.0

        sec_score = len(detected_sections) * 1.5
        compliance_score = round(wc_score + sec_score, 1)
        passed = (is_word_count_valid and len(missing_sections) == 0)
        
        feedback_parts = []
        if is_word_count_valid:
            feedback_parts.append(f"✓ Word count is valid ({word_count} words).")
        else:
            feedback_parts.append(f"✗ Word count invalid ({word_count} words; target: 250-500).")
        if not missing_sections:
            feedback_parts.append("✓ All mandatory sections present.")
        else:
            feedback_parts.append(f"✗ Missing sections: {', '.join(missing_sections)}.")
            
        stage1_out = {
            "stage": 1,
            "stage_name": "Compliance Auditor",
            "passed": passed,
            "word_count": word_count,
            "is_word_count_valid": is_word_count_valid,
            "detected_sections": detected_sections,
            "missing_sections": missing_sections,
            "compliance_score": compliance_score,
            "feedback": " ".join(feedback_parts),
            "extracted_text": extracted_text,
            "title": title,
            "student_name": student_name
        }

        context = {
            "compliance": stage1_out,
            "fallback_title": title
        }

        # Stage 2: Novelty Assessor
        stage2_out = self.stage2_novelty.evaluate(context)
        context["novelty"] = stage2_out

        # Stage 3: Technical Critic
        stage3_out = self.stage3_critic.evaluate(context)
        context["critic"] = stage3_out

        elapsed_time = round(time.time() - start_time, 4)
        triage_status = stage3_out.get("recommendation", "Needs Revision")
        final_status = stage3_out.get("final_status", "revision")

        return {
            "title": title,
            "student_name": student_name,
            "triage_status": triage_status,
            "final_status": final_status,
            "compliance": stage1_out,
            "novelty": stage2_out,
            "critic": stage3_out,
            "processing_time_seconds": elapsed_time
        }

pipeline_engine = MultiAgentPipeline()
