from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from typing import List
import time
import asyncio
import os
import logging
from dotenv import load_dotenv

from .models import ScreeningResponse, CandidateRanking
from .screener import parse_pdf_resume, score_candidate, extract_job_title, trigger_n8n_webhook

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HireSignal ⚡ Candidate Screening Intelligence",
    description="An AI-powered production-ready API for screening and ranking candidates based on a job description and their PDF resumes.",
    version="1.0.0",
    docs_url=None, # Disable default docs so we can customize it
)

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    html_content = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    ).body.decode("utf-8")
    
    dark_theme_css = """
    <style>
        body { background-color: #121212; color: #e0e0e0; }
        .swagger-ui .info .title { color: #ffffff; }
        .swagger-ui .info p { color: #b0b0b0; }
        .swagger-ui .scheme-container { background-color: #1e1e1e; }
        .swagger-ui .opblock .opblock-summary-method { color: #ffffff; }
        .swagger-ui .opblock.opblock-post { background: rgba(73, 204, 144, 0.1); border-color: #49cc90; }
        .swagger-ui .opblock.opblock-get { background: rgba(97, 175, 254, 0.1); border-color: #61affe; }
        .swagger-ui section.models { border-color: #333; background: #1e1e1e; }
        .swagger-ui section.models h4 { color: #fff; }
        .swagger-ui .model-title { color: #fff; }
        .swagger-ui .model { color: #ccc; }
        .swagger-ui .parameter__name { color: #fff; }
        .swagger-ui .parameter__type { color: #ccc; }
        .swagger-ui table thead tr th { color: #fff; }
        .swagger-ui .response-col_status { color: #fff; }
        .swagger-ui .response-col_description { color: #ccc; }
        .swagger-ui .btn { color: #fff; background: #333; }
        .swagger-ui .topbar { display: none; }
    </style>
    """
    html_content = html_content.replace("</head>", dark_theme_css + "</head>")
    return HTMLResponse(html_content)

@app.get("/health", tags=["System"])
async def health_check():
    """Returns the API status."""
    return {"status": "ok", "message": "HireSignal API is running smoothly."}

@app.post("/screen", response_model=ScreeningResponse, tags=["Screening"])
async def screen_candidates(
    background_tasks: BackgroundTasks,
    job_description: str = Form(..., description="The job description text to screen candidates against."),
    resumes: List[UploadFile] = File(..., description="Multiple PDF resume files to be evaluated.")
):
    """
    Upload a job description and multiple PDF resumes to get a ranked list of candidates.
    The response contains an ordered list of candidates with their match scores, strengths, and weaknesses.
    """
    if not resumes:
        raise HTTPException(status_code=400, detail="No resumes provided.")
        
    start_time = time.time()
    logger.info(f"Starting screening for {len(resumes)} candidates.")
    
    # 1. Extract job title
    job_title = await extract_job_title(job_description)

    # 2. Parse PDFs and score candidates concurrently
    async def process_resume(resume: UploadFile):
        file_bytes = await resume.read()
        text = await parse_pdf_resume(file_bytes)
        score = await score_candidate(job_description, text)
        return score
    
    tasks = [process_resume(resume) for resume in resumes]
    candidate_scores = await asyncio.gather(*tasks)

    # 3. Rank the candidates based on match_score descending
    sorted_scores = sorted(candidate_scores, key=lambda x: x.match_score, reverse=True)
    
    rankings = []
    for i, score in enumerate(sorted_scores, start=1):
        rankings.append(
            CandidateRanking(
                rank=i,
                name=score.name,
                match_score=score.match_score,
                strengths=score.strengths,
                weaknesses=score.weaknesses,
                recommendation=score.recommendation,
                summary=score.summary
            )
        )
    
    duration = time.time() - start_time
    screening_time = f"{duration:.1f}s"
    
    response = ScreeningResponse(
        job_title=job_title,
        total_candidates=len(rankings),
        screening_time=screening_time,
        rankings=rankings
    )
    
    # 4. Trigger n8n webhook in the background
    webhook_url = os.getenv("N8N_WEBHOOK_URL")
    if webhook_url:
        background_tasks.add_task(trigger_n8n_webhook, webhook_url, response.model_dump())
        
    logger.info(f"Screening complete in {screening_time}. Top candidate: {rankings[0].name if rankings else 'None'}")
    return response
