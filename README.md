# HireSignal ⚡ Candidate Screening Intelligence

```text
  _   _ _           _____ _                   _ 
 | | | (_)         / ____(_)                 | |
 | |_| |_ _ __ ___| (___  _  __ _ _ __   __ _| |
 |  _  | | '__/ _ \\___ \| |/ _` | '_ \ / _` | |
 | | | | | | |  __/____) | | (_| | | | | (_| | |
 \_| |_/_|_|  \___|_____/|_|\__, |_| |_|\__,_|_|
                             __/ |              
                            |___/               
```

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-009688.svg?logo=fastapi)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg?logo=docker)
![LangChain](https://img.shields.io/badge/LangChain-Integration-orange.svg)

An AI-powered production-ready API for screening and ranking candidates based on a job description and their PDF resumes.

## Features
- **AI Scoring & Ranking**: Uses LangChain and Groq's `llama-3.1-8b-instant` model to score candidates against the provided job description.
- **PDF Extraction**: Extracts text from candidate resumes automatically using PyPDF2.
- **Automated Webhooks**: Triggers an n8n webhook with a structured JSON payload containing the results when the screening is complete.
- **Dark Mode Swagger**: Enjoy a beautiful, custom dark-themed Swagger UI.
- **Dockerized**: Fully containerized with a simple `docker-compose` setup.

## Setup Instructions

1. **Clone the repository** (if applicable) and navigate to the project directory:
   ```bash
   cd hiresignal
   ```

2. **Set up Environment Variables**:
   Copy `.env.example` to `.env` and configure your API keys.
   ```bash
   cp .env.example .env
   # Edit .env and add your GROQ_API_KEY
   ```

3. **Run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```
   The API will be available at `http://localhost:8000`.

## API Usage

You can test the API directly using the [Swagger UI](http://localhost:8000/docs) or via `curl`.

### Health Check
```bash
curl -X 'GET' \
  'http://localhost:8000/health' \
  -H 'accept: application/json'
```

### Screen Candidates
```bash
curl -X 'POST' \
  'http://localhost:8000/screen' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'job_description=We are looking for a senior Python developer with experience in FastAPI, Docker, and LLMs.' \
  -F 'resumes=@/path/to/resume1.pdf;type=application/pdf' \
  -F 'resumes=@/path/to/resume2.pdf;type=application/pdf'
```

## Architecture Flow

```text
USER (Uploads JD + PDFs) 
  |
  v
FastAPI (POST /screen)
  |
  +--> Parse PDFs concurrently (PyPDF2)
  |
  +--> LLM Evaluation (LangChain + Groq llama-3.1-8b)
  |      - Extracts Job Title
  |      - Scores match (0-100)
  |      - Identifies strengths & weaknesses
  |
  +--> Ranking & Sorting
  |
  +--> Background Task: POST results to n8n Webhook
  |
  v
Return JSON Response (Ranked Candidates)
```

## n8n Integration
When the screening completes, the API fires an async HTTP POST request to the configured `N8N_WEBHOOK_URL`. The payload is the exact JSON response returned by the API. You can set up an n8n workflow using a Webhook Trigger node to receive this data and send emails, update an ATS, or post to Slack.
