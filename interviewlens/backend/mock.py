import json
import os
import time

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

app = FastAPI(title="InterviewLens Mock Interview AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://karanaldo-07.github.io",
        "http://localhost:3000",
        "http://127.0.0.1:5500",
    ],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

_RATE = {}


def rate_limit(request: Request, limit=12, window=600):
    ip = (request.headers.get("x-forwarded-for") or request.client.host or "unknown").split(",")[0].strip()
    now = time.time()
    hits = [t for t in _RATE.get(ip, []) if now - t < window]
    if len(hits) >= limit:
        raise HTTPException(429, "Too many AI evaluations. Please try again later.")
    hits.append(now)
    _RATE[ip] = hits
    if len(_RATE) > 2000:
        for key in list(_RATE)[:500]:
            _RATE.pop(key, None)


class MockEvaluateRequest(BaseModel):
    role: str = Field(default="Software Engineer", max_length=120)
    job_description: str = Field(default="", max_length=12000)
    question: str = Field(min_length=3, max_length=1000)
    answer: str = Field(min_length=5, max_length=12000)


SCHEMA = {
    "type": "object",
    "properties": {
        "total": {"type": "integer", "minimum": 0, "maximum": 100},
        "relevance": {"type": "integer", "minimum": 0, "maximum": 30},
        "completeness": {"type": "integer", "minimum": 0, "maximum": 30},
        "structure": {"type": "integer", "minimum": 0, "maximum": 20},
        "specificity": {"type": "integer", "minimum": 0, "maximum": 20},
        "strengths": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 4},
        "improvements": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 4},
        "strong_answer_direction": {"type": "string"},
    },
    "required": [
        "total", "relevance", "completeness", "structure", "specificity",
        "strengths", "improvements", "strong_answer_direction"
    ],
}


@app.get("/health")
def health():
    return {"status": "ok", "provider": "gemini", "configured": bool(GEMINI_API_KEY), "model": GEMINI_MODEL}


@app.post("/evaluate")
def evaluate(req: MockEvaluateRequest, request: Request):
    rate_limit(request)
    if not GEMINI_API_KEY:
        raise HTTPException(503, "AI evaluator is not configured. Local evaluation remains available.")

    prompt = f"""You are an expert technical interviewer evaluating a candidate's answer.
Return ONLY the requested JSON structure.

Role: {req.role}
Job description (may be empty): {req.job_description[:8000]}
Interview question: {req.question}
Candidate answer: {req.answer}

Scoring rubric:
- relevance /30: directly addresses what the question asks; do not reward keyword stuffing.
- completeness /30: covers the important reasoning, steps, concepts, edge cases, or result appropriate to the question.
- structure /20: clear, logical, easy-to-follow explanation; use STAR for behavioral questions when appropriate.
- specificity /20: concrete examples, technologies, metrics, constraints, trade-offs, or personal contribution when appropriate.

Be fair to junior candidates: concise answers can still score well when technically correct and directly useful. Do not invent facts about the candidate. For coding/technical questions, prioritize correctness and reasoning. For behavioral questions, prioritize the candidate's own actions and outcomes.
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
            "responseSchema": SCHEMA,
        },
    }

    try:
        response = requests.post(
            url,
            headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
            json=body,
            timeout=25,
        )
        response.raise_for_status()
        payload = response.json()
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
    except (requests.RequestException, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(502, f"AI evaluation failed: {type(exc).__name__}") from exc

    result["total"] = max(0, min(100, int(result["total"])))
    result["relevance"] = max(0, min(30, int(result["relevance"])))
    result["completeness"] = max(0, min(30, int(result["completeness"])))
    result["structure"] = max(0, min(20, int(result["structure"])))
    result["specificity"] = max(0, min(20, int(result["specificity"])))
    result["source"] = "gemini"
    result["model"] = GEMINI_MODEL
    return result
