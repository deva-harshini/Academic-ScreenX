import re
from typing import Dict, Any, List
from app.agents.base import BaseAgent
from app.schemas import CriticResult

class TechnicalCritic(BaseAgent):
    """
    Stage 3 Agent:
    Performs rigorous peer review scoring S ∈ [1, 10], evaluates dataset feasibility,
    identifies technical strengths & weaknesses, and writes a strict 3-sentence executive summary review.
    """
    def __init__(self):
        super().__init__(name="Technical Critic", role="Stage 3 Methodological Rigor & Feasibility Scorer")

    def evaluate_dataset_feasibility(self, text: str) -> Dict[str, str]:
        lower_text = text.lower()

        # Check for specific dataset keywords or edge constraints
        if any(term in lower_text for term in ["proprietary", "classified", "unreleased patient", "billion parameters", "10,000 gpus"]):
            return {
                "feasibility": "Low",
                "analysis": "Dataset or compute requirements appear restrictive for standard student lab resources without external corporate/hospital grant clearance."
            }
        elif any(term in lower_text for term in ["physionet", "mit-bih", "cifar", "imagenet", "arxiv", "mimic", "synthetic", "open-source", "kaggle", "benchmarks", "github", "publicly available"]):
            return {
                "feasibility": "High",
                "analysis": "Identifies accessible open-access academic benchmarks and standard research datasets, enabling immediate verification and reproducibility."
            }
        elif any(term in lower_text for term in ["simulated", "custom dataset", "collected from 50 participants", "survey", "scraped"]):
            return {
                "feasibility": "Moderate",
                "analysis": "Relies on student-collected or simulated data; protocol is feasible but requires clear IRB/data hygiene protocols."
            }
        else:
            return {
                "feasibility": "Moderate",
                "analysis": "Dataset source is implicitly described; standard academic benchmark datasets can be substituted for validation."
            }

    def compute_technical_scores(self, compliance: Dict[str, Any], novelty: Dict[str, Any], text: str) -> Dict[str, Any]:
        comp_score = compliance.get("compliance_score", 5.0)
        nov_score = novelty.get("novelty_score", 5.0)
        
        # Rigor heuristics
        has_metrics = bool(re.search(r"(?i)(accuracy|f1-score|latency|flops|loss|auc|roc|bleu|p-value|rmse)", text))
        has_baseline = bool(re.search(r"(?i)(baseline|compared to|benchmark|state-of-the-art|sota|prior work)", text))
        has_math = bool(re.search(r"(\$|\\|\+|\-|\=|\bargmax\b|\bsum\b|\bsigma\b)", text))
        
        depth = 5.0
        if has_metrics: depth += 2.0
        if has_baseline: depth += 1.5
        if has_math: depth += 1.0
        depth = min(10.0, max(2.0, depth))

        rigor = 5.5
        if comp_score >= 8.0: rigor += 1.5
        if nov_score >= 7.0: rigor += 1.5
        if not novelty.get("is_novel", True): rigor -= 3.0
        rigor = min(10.0, max(2.0, round(rigor, 1)))

        # Weighted composite score S in [1, 10]
        # Formula: 25% Compliance + 45% Novelty + 30% Rigor
        composite = (0.25 * comp_score) + (0.45 * nov_score) + (0.30 * rigor)
        overall_score = min(10.0, max(1.0, round(composite, 1)))

        return {
            "overall_score": overall_score,
            "technical_depth_score": round(depth, 1),
            "methodology_rigor_score": round(rigor, 1)
        }

    def generate_three_sentence_summary(
        self,
        title: str,
        student_name: str,
        compliance: Dict[str, Any],
        novelty: Dict[str, Any],
        scores: Dict[str, Any],
        feasibility: Dict[str, str],
        recommendation: str
    ) -> str:
        """
        Enforces exactly 3 sentences:
        Sentence 1: Context and methodology summary.
        Sentence 2: Critical assessment of feasibility, experimental design, and novelty.
        Sentence 3: Faculty recommendation and action.
        """
        # Clean trailing dots and whitespace from inputs
        clean_method = re.sub(r'[\.\s]+$', '', novelty.get('extracted_methodology', 'a structured computational framework')[:120].strip())
        
        # Sentence 1: Core concept
        s1 = f"This proposal titled '{title}' investigates a method utilizing {clean_method}."
        
        # Sentence 2: Feasibility & Novelty Evaluation
        if not compliance.get("passed", False):
            s2 = f"While the concept is presented, the submission suffers from structural formatting deficits, missing sections ({', '.join(compliance.get('missing_sections', [])) or 'word count violation'}), and requires formal cleanup."
        elif not novelty.get("is_novel", False):
            s2 = f"The proposed pipeline exhibits high redundancy with saturated baseline tutorials ({novelty.get('verdict', 'low novelty')}), offering minimal theoretical or algorithmic advancement."
        else:
            s2 = f"The methodological approach demonstrates strong technical rigor, favorable dataset feasibility ({feasibility['feasibility']}), and a distinct architectural contribution over prior benchmarks."

        # Sentence 3: Faculty Action
        if recommendation == "Approved for Faculty":
            s3 = f"The proposal is officially recommended for faculty advancement and lab project allocation with an overall score of {scores['overall_score']} out of 10."
        elif recommendation == "Flagged for Low Novelty":
            s3 = f"The committee flags this submission for low novelty and advises the student to incorporate original feature engineering or explore a novel research problem."
        else: # Needs Revision
            s3 = f"The student should revise the abstract to satisfy formatting criteria (250-500 words and all 4 mandatory sections) prior to final faculty consideration."

        return f"{s1} {s2} {s3}"

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        compliance = context.get("compliance", {})
        novelty = context.get("novelty", {})
        extracted_text = compliance.get("extracted_text", "")
        title = compliance.get("title", "Academic Proposal")
        student_name = compliance.get("student_name", "Student Researcher")

        feasibility_info = self.evaluate_dataset_feasibility(extracted_text)
        scores = self.compute_technical_scores(compliance, novelty, extracted_text)

        strengths = []
        weaknesses = []

        if compliance.get("is_word_count_valid", False):
            strengths.append(f"Optimal abstract length ({compliance.get('word_count')} words).")
        else:
            weaknesses.append(f"Non-compliant word count ({compliance.get('word_count')} words; required: 250-500).")

        if not compliance.get("missing_sections"):
            strengths.append("Complete structural composition across all four mandatory academic sections.")
        else:
            weaknesses.append(f"Missing core section headers: {', '.join(compliance.get('missing_sections', []))}.")

        if novelty.get("is_novel", False):
            strengths.append(f"High methodological novelty ({novelty.get('novelty_score')}/10) with clear differentiator.")
        else:
            weaknesses.append(f"Duplicate/saturated topic risk ({novelty.get('verdict')}).")

        if feasibility_info["feasibility"] == "High":
            strengths.append("High dataset accessibility and empirical reproducibility.")
        else:
            weaknesses.append(f"Data feasibility is {feasibility_info['feasibility']} - may require resource allocation.")

        # Determine Recommendation category
        if not novelty.get("is_novel", True):
            recommendation = "Flagged for Low Novelty"
            status_code = "flagged"
        elif not compliance.get("passed", False):
            recommendation = "Needs Revision"
            status_code = "revision"
        else:
            if scores["overall_score"] >= 6.0:
                recommendation = "Approved for Faculty"
                status_code = "approved"
            else:
                recommendation = "Needs Revision"
                status_code = "revision"

        summary_review = self.generate_three_sentence_summary(
            title=title,
            student_name=student_name,
            compliance=compliance,
            novelty=novelty,
            scores=scores,
            feasibility=feasibility_info,
            recommendation=recommendation
        )

        result = CriticResult(
            overall_score=scores["overall_score"],
            technical_depth_score=scores["technical_depth_score"],
            methodology_rigor_score=scores["methodology_rigor_score"],
            dataset_feasibility=feasibility_info["feasibility"],
            dataset_analysis=feasibility_info["analysis"],
            summary_review=summary_review,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendation=recommendation
        )

        output = result.model_dump()
        output["final_status"] = status_code
        return output
