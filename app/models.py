from pydantic import BaseModel, Field
from typing import List

class CandidateScore(BaseModel):
    name: str = Field(default="Unknown", description="Name of the candidate extracted from the resume")
    match_score: int = Field(default=0, description="Match score out of 100 based on the job description")
    strengths: List[str] = Field(default_factory=list, description="List of strengths identified in the resume matching the job description")
    weaknesses: List[str] = Field(default_factory=list, description="List of weaknesses or missing skills")
    recommendation: str = Field(default="", description="Hiring recommendation (e.g., 'Strongly Recommend', 'Recommend', 'Do Not Recommend')")
    summary: str = Field(default="", description="A 2-line summary of the candidate's fit for the role")

class CandidateRanking(CandidateScore):
    rank: int = Field(..., description="The candidate's rank based on their match score")

class ScreeningResponse(BaseModel):
    job_title: str = Field(..., description="Job title extracted from the Job Description")
    total_candidates: int = Field(..., description="Total number of candidates screened")
    screening_time: str = Field(..., description="Time taken to screen candidates (e.g., '2.3s')")
    rankings: List[CandidateRanking] = Field(..., description="List of candidates ordered by rank")
