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
        raise HTTPException(429, "Too many AI requests. Please try again later.")
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


class NextQuestionRequest(BaseModel):
    role: str = Field(default="Software Engineer", max_length=120)
    job_description: str = Field(default="", max_length=12000)
    current_question: str = Field(min_length=3, max_length=1000)
    candidate_answer: str = Field(min_length=5, max_length=12000)
    evaluation: dict
    asked_questions: list[str] = Field(default_factory=list, max_length=10)
    question_number: int = Field(default=1, ge=1, le=10)
    total_questions: int = Field(default=5, ge=1, le=10)


class ReportRequest(BaseModel):
    role: str = Field(default="Software Engineer", max_length=120)
    job_description: str = Field(default="", max_length=12000)
    results: list[dict] = Field(min_length=1, max_length=10)
    questions: list[str] = Field(default_factory=list, max_length=10)


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
    "required": ["total", "relevance", "completeness", "structure", "specificity", "strengths", "improvements", "strong_answer_direction"],
}

NEXT_SCHEMA = {
    "type": "object",
    "properties": {
        "next_question": {"type": "string", "minLength": 5, "maxLength": 1000},
        "category": {"type": "string", "enum": ["Technical", "Coding", "System Design", "Behavioral", "Problem Solving", "Role-specific"]},
        "difficulty": {"type": "string", "enum": ["Easy", "Medium", "Hard"]},
        "reason": {"type": "string", "maxLength": 500},
    },
    "required": ["next_question", "category", "difficulty", "reason"],
}

REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "readiness": {"type": "string", "enum": ["Not ready yet", "Developing", "Interview-ready", "Strongly interview-ready"]},
        "headline": {"type": "string", "maxLength": 180},
        "summary": {"type": "string", "maxLength": 700},
        "strengths": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 5},
        "weak_areas": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 5},
        "priority_topics": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 6},
        "action_plan": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 6},
        "next_questions": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 5},
    },
    "required": ["readiness", "headline", "summary", "strengths", "weak_areas", "priority_topics", "action_plan", "next_questions"],
}


def gemini_json(prompt: str, schema: dict):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json", "responseSchema": schema},
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
        return json.loads(text)
    except (requests.RequestException, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(502, f"AI request failed: {type(exc).__name__}") from exc


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
- completeness /30: covers important reasoning, steps, concepts, edge cases, or result appropriate to the question.
- structure /20: clear, logical, easy-to-follow explanation; use STAR for behavioral questions when appropriate.
- specificity /20: concrete examples, technologies, metrics, constraints, trade-offs, or personal contribution when appropriate.

Be fair to junior candidates. Concise answers can score well when correct. Do not invent facts. For coding/technical questions prioritize correctness and reasoning; for behavioral questions prioritize the candidate's own actions and outcomes.
"""
    result = gemini_json(prompt, SCHEMA)
    for key, cap in [("total", 100), ("relevance", 30), ("completeness", 30), ("structure", 20), ("specificity", 20)]:
        result[key] = max(0, min(cap, int(result[key])))
    result["source"] = "gemini"
    result["model"] = GEMINI_MODEL
    return result


@app.post("/next")
def next_question(req: NextQuestionRequest, request: Request):
    rate_limit(request)
    if not GEMINI_API_KEY:
        raise HTTPException(503, "AI interviewer is not configured.")
    asked = "\n".join(f"- {q}" for q in req.asked_questions[-10:]) or "- none"
    evaluation = json.dumps(req.evaluation, ensure_ascii=False)[:4000]
    prompt = f"""You are the adaptive interviewer in a realistic {req.role} interview.
Generate exactly one next interview question as JSON.

Role: {req.role}
Job description: {req.job_description[:7000]}
Current question: {req.current_question}
Candidate answer: {req.candidate_answer[:7000]}
Evaluation of current answer: {evaluation}
Questions already asked:
{asked}

This is question {req.question_number} of {req.total_questions}.

Rules:
- Adapt difficulty to the answer: strong answers should get a deeper follow-up or harder adjacent topic; weak answers should get a focused clarifying question or a simpler foundation check.
- Do not repeat an already asked question.
- Stay relevant to the role and job description.
- Mix technical, coding/problem-solving, system-design, and behavioral topics when appropriate.
- A follow-up should test understanding, not merely rephrase the previous question.
- Keep the question answerable in 1-3 minutes.
- If the candidate has a clear weakness, target that weakness next.
- Return only JSON matching the schema.
"""
    result = gemini_json(prompt, NEXT_SCHEMA)
    result["source"] = "gemini"
    result["model"] = GEMINI_MODEL
    return result


@app.post("/report")
def report(req: ReportRequest, request: Request):
    rate_limit(request)
    if not GEMINI_API_KEY:
        raise HTTPException(503, "AI report is not configured.")
    compact_results = json.dumps(req.results, ensure_ascii=False)[:12000]
    compact_questions = json.dumps(req.questions, ensure_ascii=False)[:6000]
    prompt = f"""You are the senior interviewer producing a final candidate report after a mock interview.
Return ONLY JSON matching the schema.

Role: {req.role}
Job description: {req.job_description[:7000]}
Questions asked: {compact_questions}
Per-question evaluation results: {compact_results}

Rules:
- Base conclusions on the supplied evaluations. Do not invent candidate experience, technologies, or facts.
- Readiness must reflect the overall performance, not one unusually good or bad answer.
- Identify recurring weak dimensions and convert them into concrete revision topics.
- Prioritize role/JD-relevant topics.
- Make the action plan practical and ordered.
- Next questions should specifically target the candidate's weak areas.
- Be concise and honest; this is a coaching report, not praise for its own sake.
"""
    result = gemini_json(prompt, REPORT_SCHEMA)
    result["source"] = "gemini"
    result["model"] = GEMINI_MODEL
    return result
