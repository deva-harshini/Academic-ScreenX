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
pipeline_engine = MultiAgentPipeline()
