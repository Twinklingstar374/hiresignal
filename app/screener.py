
import io
import httpx
import logging
from PyPDF2 import PdfReader
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from .models import CandidateScore

logger = logging.getLogger(__name__)

async def parse_pdf_resume(file_bytes: bytes) -> str:
    """Extracts text from a PDF resume."""
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error parsing PDF: {e}")
        return ""

async def score_candidate(job_description: str, resume_text: str) -> CandidateScore:
    """Scores a candidate's resume against a job description using Groq LLM."""
    if not resume_text:
        return CandidateScore(
            name="Unreadable/Empty Resume",
            match_score=0,
            strengths=[],
            weaknesses=["Could not read resume content"],
            recommendation="Do Not Recommend",
            summary="The provided resume could not be parsed or was empty."
        )

    # Note: Ensure GROQ_API_KEY is in the environment
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.0,
        max_retries=2
    )

    prompt = PromptTemplate.from_template(
        """You are an expert technical recruiter and HR assistant. 
Your task is to evaluate a candidate's resume against the provided job description.
Be objective, thorough, and highly accurate in your assessment.

Job Description:
{job_description}

Candidate Resume:
{resume_text}

Analyze the resume and provide the following:
1. Candidate Name (if not found, use "Unknown")
2. Match Score (0 to 100 integer based on how well their skills/experience match the JD)
3. Strengths (List of matching skills/experiences)
4. Weaknesses (List of missing skills or experience gaps)
5. Recommendation (e.g., "Strongly Recommend", "Recommend", "Do Not Recommend")
6. Summary (A concise 2-line summary of their fit)
"""
    )
    
    chain = prompt | llm.with_structured_output(CandidateScore)
    
    try:
        result = await chain.ainvoke({"job_description": job_description, "resume_text": resume_text})
        return result
    except Exception as e:
        logger.error(f"Error scoring candidate with Groq: {e}")
        return CandidateScore(
            name="Error Processing Candidate",
            match_score=0,
            strengths=[],
            weaknesses=[f"Error during AI processing: {str(e)}"],
            recommendation="Review Manually",
            summary="An error occurred while evaluating this candidate."
        )

async def extract_job_title(job_description: str) -> str:
    """Extracts the job title from the job description."""
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.0, max_retries=2)
    prompt = PromptTemplate.from_template("Extract only the job title from this job description. If none is found, return 'Unknown Position'.\n\nJob Description:\n{job_description}")
    chain = prompt | llm
    try:
        res = await chain.ainvoke({"job_description": job_description})
        return res.content.strip()
    except Exception:
        return "Unknown Position"

async def trigger_n8n_webhook(webhook_url: str, payload: dict):
    """Sends a POST request with the screening results to the configured n8n webhook."""
    if not webhook_url:
        logger.warning("No n8n webhook URL configured. Skipping webhook trigger.")
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload, timeout=10.0)
            response.raise_for_status()
            logger.info(f"Successfully triggered n8n webhook: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to trigger n8n webhook: {e}")
