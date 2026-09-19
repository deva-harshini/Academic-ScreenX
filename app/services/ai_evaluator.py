"""
AI-Powered RAG (Retrieval-Augmented Generation) Document Evaluation Layer.

This module provides end-to-end vector indexing and automated criteria-based evaluation
for academic proposals, job applicant documents, and research papers (PDF and TXT).

Architecture:
1. Document Ingestion: Loads PDF (PyPDFLoader) or TXT (TextLoader).
2. Semantic Chunking: RecursiveCharacterTextSplitter (chunk_size=500, chunk_overlap=50).
3. Vector Indexing: InMemoryVectorStore / Chroma with OpenAIEmbeddings (or local fallback).
4. RAG Retrieval Chain: ChatOpenAI (gpt-4o-mini) with structured prompt evaluation.
5. Structured Output:
   - Match Status: "Qualified" | "Not Qualified" | "Needs Review"
   - Key Evidence Found: Concrete factual citations retrieved from document chunks.
   - Missing Requirements: Unmet criteria or gaps identified during retrieval analysis.
"""

import os
import json
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

# LangChain core & document loaders
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.documents import Document

try:
    from langchain_core.vectorstores import InMemoryVectorStore
    HAS_IN_MEMORY_STORE = True
except ImportError:
    HAS_IN_MEMORY_STORE = False

try:
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from langchain_community.vectorstores import Chroma
    HAS_CHROMA = True
except (ImportError, Exception):
    HAS_CHROMA = False

logger = logging.getLogger("AcademicScreenX.AIEvaluator")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

DEFAULT_ACADEMIC_CRITERIA = """
1. Clear Research Hypothesis & Problem Statement: The proposal must state a precise problem and research objective.
2. Methodological Rigor: Clear technical approach, dataset description, and evaluation metrics.
3. Novelty & Academic Contribution: Demonstrates unique angle or advancement over existing state-of-the-art.
4. Feasibility & Ethical Compliance: Realistic execution scope with adequate computational resources and dataset accessibility.
"""

def _load_document_chunks(file_path: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[Document]:
    """
    Loads a PDF or TXT file and splits it into semantic chunks.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Document not found at path: {file_path}")

    ext = path.suffix.lower()
    docs = []

    if ext == ".pdf":
        loader = PyPDFLoader(str(path))
        docs = loader.load()
    elif ext in (".txt", ".md", ".csv", ".json"):
        loader = TextLoader(str(path), encoding="utf-8")
        docs = loader.load()
    else:
        # Fallback loader
        try:
            loader = PyPDFLoader(str(path))
            docs = loader.load()
        except Exception:
            loader = TextLoader(str(path), encoding="utf-8")
            docs = loader.load()

    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = text_splitter.split_documents(docs)
    return chunks

def _mock_heuristic_evaluation(chunks: List[Document], criteria: str, file_path: str) -> Dict[str, Any]:
    """
    Deterministic fallback evaluation when OpenAI API key is unavailable or in mock mode.
    Performs keyword & semantic section matching across document chunks.
    """
    combined_text = " ".join([c.page_content for c in chunks])
    lower_text = combined_text.lower()
    
    # Check for presence of essential academic/job sections
    has_methodology = any(w in lower_text for w in ["methodology", "method", "architecture", "algorithm", "model", "approach"])
    has_results = any(w in lower_text for w in ["results", "evaluation", "metrics", "accuracy", "performance", "benchmark"])
    has_dataset = any(w in lower_text for w in ["dataset", "data", "corpus", "samples", "benchmark", "cifar", "imagenet"])
    has_intro = any(w in lower_text for w in ["introduction", "background", "motivation", "objective", "problem"])
    has_conclusion = any(w in lower_text for w in ["conclusion", "future work", "summary", "discussion"])

    evidence_points = []
    missing_points = []

    if has_intro:
        evidence_points.append("Clear problem context and research motivation identified in initial sections.")
    else:
        missing_points.append("Lacks well-defined introduction or explicit problem formulation.")

    if has_methodology:
        evidence_points.append("Technical methodology and algorithmic architecture details described.")
    else:
        missing_points.append("Missing concrete methodology or technical implementation details.")

    if has_dataset:
        evidence_points.append("Dataset specifications, data acquisition pipeline, or benchmarks referenced.")
    else:
        missing_points.append("No explicit dataset feasibility or source mentioned.")

    if has_results:
        evidence_points.append("Empirical evaluation metrics, baseline comparisons, or expected outcomes present.")
    else:
        missing_points.append("Limited quantitative evaluation metrics or validation framework.")

    # Determine status
    if len(missing_points) == 0:
        match_status = "Qualified"
    elif len(missing_points) <= 2:
        match_status = "Needs Review"
    else:
        match_status = "Not Qualified"

    # Sample key snippets as evidence
    sample_snippets = [c.page_content[:180].strip().replace("\n", " ") + "..." for c in chunks[:3] if c.page_content.strip()]

    return {
        "Match Status": match_status,
        "Key Evidence Found": evidence_points if evidence_points else ["Initial abstract text provided."],
        "Missing Requirements": missing_points if missing_points else ["None. All core criteria satisfied."],
        "metadata": {
            "document_name": Path(file_path).name,
            "total_chunks": len(chunks),
            "evaluation_mode": "Deterministic Heuristic RAG Fallback",
            "retrieved_evidence_snippets": sample_snippets
        }
    }

def evaluate_document(file_path: str, evaluation_criteria: Optional[str] = None) -> Dict[str, Any]:
    """
    Evaluates a candidate document (PDF or TXT) against specific criteria using LangChain RAG.

    Args:
        file_path (str): Path to the uploaded document file.
        evaluation_criteria (str, optional): The job or academic evaluation criteria.
                                            Defaults to standard academic proposal guidelines.

    Returns:
        dict: A structured dictionary containing:
            - "Match Status": "Qualified" | "Not Qualified" | "Needs Review"
            - "Key Evidence Found": List of evidence statements/citations
            - "Missing Requirements": List of missing items or areas for revision
            - "metadata": Additional processing details and chunk statistics
    """
    criteria = evaluation_criteria or DEFAULT_ACADEMIC_CRITERIA
    logger.info(f"Starting AI RAG document evaluation for: {file_path}")

    # 1. Ingest and split document
    try:
        chunks = _load_document_chunks(file_path, chunk_size=500, chunk_overlap=50)
    except Exception as e:
        logger.error(f"Failed to load or chunk document {file_path}: {e}")
        return {
            "Match Status": "Needs Review",
            "Key Evidence Found": [],
            "Missing Requirements": [f"Document parsing error: {str(e)}"],
            "metadata": {"error": str(e), "document_path": file_path}
        }

    if not chunks:
        return {
            "Match Status": "Not Qualified",
            "Key Evidence Found": [],
            "Missing Requirements": ["Document contains no readable text."],
            "metadata": {"total_chunks": 0, "document_path": file_path}
        }

    # 2. Check OpenAI API key and Mock mode configuration
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    use_mock = os.getenv("USE_MOCK_LLM", "True").lower() in ("true", "1", "yes")

    # If mock mode or no API key, execute robust local RAG fallback
    if not openai_key or use_mock or not HAS_OPENAI:
        logger.info("Using local heuristic RAG evaluation engine (Offline/Mock Mode).")
        return _mock_heuristic_evaluation(chunks, criteria, file_path)

    # 3. Vector store indexing & OpenAI RAG chain
    try:
        embeddings = OpenAIEmbeddings(
            openai_api_key=openai_key,
            model="text-embedding-3-small"
        )
        
        # Use fast InMemoryVectorStore or Chroma
        if HAS_IN_MEMORY_STORE:
            vectorstore = InMemoryVectorStore.from_documents(
                documents=chunks,
                embedding=embeddings
            )
        elif HAS_CHROMA:
            temp_persist_dir = tempfile.mkdtemp(prefix="chroma_screenx_")
            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                persist_directory=temp_persist_dir,
                collection_name=f"eval_{uuid.uuid4().hex[:8]}"
            )
        else:
            return _mock_heuristic_evaluation(chunks, criteria, file_path)

        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": min(4, len(chunks))}
        )

        # Retrieve relevant chunks for criteria
        retrieved_docs = retriever.invoke(criteria)
        context_text = "\n\n---\n\n".join([doc.page_content for doc in retrieved_docs])

        # 4. LLM Evaluation Prompt with ChatOpenAI (gpt-4o-mini)
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            openai_api_key=openai_key
        )

        system_prompt = """You are an expert academic evaluator and screening officer.
You will evaluate the following candidate document excerpt against the provided Evaluation Criteria.

Evaluation Criteria:
{criteria}

Candidate Document Context:
{context}

Provide your evaluation strictly as a valid JSON object matching this exact structure:
{{
  "Match Status": "Qualified" | "Not Qualified" | "Needs Review",
  "Key Evidence Found": [
    "Evidence statement 1 with factual basis from text",
    "Evidence statement 2 with factual basis from text"
  ],
  "Missing Requirements": [
    "Requirement 1 that is missing or insufficiently addressed",
    "Requirement 2 that is missing or insufficiently addressed"
  ]
}}

Ensure "Match Status" is one of: "Qualified", "Not Qualified", "Needs Review".
Return ONLY the JSON object. Do not include markdown code fences or extra text."""

        prompt = ChatPromptTemplate.from_template(system_prompt)
        chain = prompt | llm | JsonOutputParser()

        raw_result = chain.invoke({
            "criteria": criteria,
            "context": context_text
        })

        # Standardize return format
        match_status = raw_result.get("Match Status") or raw_result.get("match_status") or "Needs Review"
        if match_status not in ["Qualified", "Not Qualified", "Needs Review"]:
            match_status = "Needs Review"

        key_evidence = raw_result.get("Key Evidence Found") or raw_result.get("key_evidence_found") or []
        if isinstance(key_evidence, str):
            key_evidence = [key_evidence]

        missing_reqs = raw_result.get("Missing Requirements") or raw_result.get("missing_requirements") or []
        if isinstance(missing_reqs, str):
            missing_reqs = [missing_reqs]

        return {
            "Match Status": match_status,
            "Key Evidence Found": key_evidence,
            "Missing Requirements": missing_reqs,
            "metadata": {
                "document_name": Path(file_path).name,
                "total_chunks": len(chunks),
                "retrieved_chunks_count": len(retrieved_docs),
                "model_used": "gpt-4o-mini",
                "evaluation_mode": "LangChain OpenAI RAG Chain"
            }
        }

    except Exception as e:
        logger.warning(f"Error during OpenAI RAG execution ({e}), falling back to heuristic evaluation.")
        return _mock_heuristic_evaluation(chunks, criteria, file_path)

if __name__ == "__main__":
    import sys
    test_file = sys.argv[1] if len(sys.argv) > 1 else "sample_pdfs/03_innovative_idea.pdf"
    res = evaluate_document(test_file)
    print(json.dumps(res, indent=2))
