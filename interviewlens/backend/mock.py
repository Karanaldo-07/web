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
app.add_middleware(CORSMiddleware, allow_origins=["https://karanaldo-07.github.io", "http://localhost:3000", "http://127.0.0.1:5500"], allow_methods=["GET","POST","OPTIONS"], allow_headers=["Content-Type"])
_RATE={}
def rate_limit(request: Request, limit=12, window=600):
    ip=(request.headers.get("x-forwarded-for") or request.client.host or "unknown").split(",")[0].strip(); now=time.time(); hits=[t for t in _RATE.get(ip,[]) if now-t<window]
    if len(hits)>=limit: raise HTTPException(429,"Too many AI requests. Please try again later.")
    hits.append(now); _RATE[ip]=hits

class MockEvaluateRequest(BaseModel):
    role:str=Field(default="Software Engineer",max_length=120); job_description:str=Field(default="",max_length=12000); question:str=Field(min_length=3,max_length=1000); answer:str=Field(min_length=5,max_length=12000)
class NextQuestionRequest(BaseModel):
    role:str=Field(default="Software Engineer",max_length=120); job_description:str=Field(default="",max_length=12000); current_question:str=Field(min_length=3,max_length=1000); candidate_answer:str=Field(min_length=5,max_length=12000); evaluation:dict; asked_questions:list[str]=Field(default_factory=list,max_length=10); question_number:int=Field(default=1,ge=1,le=10); total_questions:int=Field(default=5,ge=1,le=10)
class ReportRequest(BaseModel):
    role:str=Field(default="Software Engineer",max_length=120); job_description:str=Field(default="",max_length=12000); results:list[dict]=Field(min_length=1,max_length=10); questions:list[str]=Field(default_factory=list,max_length=10)

SCHEMA={"type":"object","properties":{"total":{"type":"integer","minimum":0,"maximum":100},"relevance":{"type":"integer","minimum":0,"maximum":30},"completeness":{"type":"integer","minimum":0,"maximum":30},"structure":{"type":"integer","minimum":0,"maximum":20},"specificity":{"type":"integer","minimum":0,"maximum":20},"strengths":{"type":"array","items":{"type":"string"},"minItems":1,"maxItems":4},"improvements":{"type":"array","items":{"type":"string"},"minItems":1,"maxItems":4},"strong_answer_direction":{"type":"string"}},"required":["total","relevance","completeness","structure","specificity","strengths","improvements","strong_answer_direction"]}
NEXT_SCHEMA={"type":"object","properties":{"next_question":{"type":"string","minLength":5,"maxLength":1000},"category":{"type":"string","enum":["Technical","Coding","System Design","Behavioral","Problem Solving","Role-specific"]},"difficulty":{"type":"string","enum":["Easy","Medium","Hard"]},"reason":{"type":"string","maxLength":500}},"required":["next_question","category","difficulty","reason"]}
REPORT_SCHEMA={"type":"object","properties":{"readiness":{"type":"string","enum":["Not ready yet","Developing","Interview-ready","Strongly interview-ready"]},"headline":{"type":"string","maxLength":180},"summary":{"type":"string","maxLength":700},"strengths":{"type":"array","items":{"type":"string"},"minItems":2,"maxItems":5},"weak_areas":{"type":"array","items":{"type":"string"},"minItems":2,"maxItems":5},"priority_topics":{"type":"array","items":{"type":"string"},"minItems":2,"maxItems":6},"action_plan":{"type":"array","items":{"type":"string"},"minItems":3,"maxItems":6},"next_questions":{"type":"array","items":{"type":"string"},"minItems":3,"maxItems":5}},"required":["readiness","headline","summary","strengths","weak_areas","priority_topics","action_plan","next_questions"]}

def gemini_json(prompt,schema):
    try:
        r=requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",headers={"x-goog-api-key":GEMINI_API_KEY,"Content-Type":"application/json"},json={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.2,"responseMimeType":"application/json","responseSchema":schema}},timeout=25); r.raise_for_status(); return json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
    except (requests.RequestException,KeyError,IndexError,TypeError,json.JSONDecodeError) as exc: raise HTTPException(502,f"AI request failed: {type(exc).__name__}") from exc

@app.get("/health")
@app.get("/mock/health")
def health(): return {"status":"ok","provider":"gemini","configured":bool(GEMINI_API_KEY),"model":GEMINI_MODEL}
@app.post("/evaluate")
@app.post("/mock/evaluate")
def evaluate(req:MockEvaluateRequest,request:Request):
    rate_limit(request)
    if not GEMINI_API_KEY: raise HTTPException(503,"AI evaluator is not configured. Local evaluation remains available.")
    prompt=f"""You are an expert technical interviewer evaluating a candidate's answer. Return ONLY the requested JSON structure.
Role: {req.role}
Job description: {req.job_description[:8000]}
Interview question: {req.question}
Candidate answer: {req.answer}
Score relevance /30, completeness /30, structure /20, specificity /20. Be fair to junior candidates. Do not invent facts. Concise correct answers can score well. For behavioral questions prioritize the candidate's own actions and outcomes."""
    x=gemini_json(prompt,SCHEMA)
    for k,c in [("total",100),("relevance",30),("completeness",30),("structure",20),("specificity",20)]: x[k]=max(0,min(c,int(x[k])))
    x.update(source="gemini",model=GEMINI_MODEL); return x

@app.post("/adaptive")
def adaptive(req:NextQuestionRequest,request:Request):
    rate_limit(request)
    if not GEMINI_API_KEY: raise HTTPException(503,"AI interviewer is not configured.")
    asked="\n".join(f"- {q}" for q in req.asked_questions[-10:]) or "- none"; evaluation=json.dumps(req.evaluation,ensure_ascii=False)[:4000]
    prompt=f"""You are the adaptive interviewer in a realistic {req.role} interview. Generate exactly one next interview question as JSON.
Role: {req.role}
Job description: {req.job_description[:7000]}
Current question: {req.current_question}
Candidate answer: {req.candidate_answer[:7000]}
Evaluation: {evaluation}
Questions already asked:\n{asked}
This is question {req.question_number} of {req.total_questions}.
Adapt difficulty: strong answers get a deeper follow-up or harder adjacent topic; weak answers get a focused clarifying question or simpler foundation check. Never repeat. Stay role/JD relevant. Mix technical, coding/problem-solving, system-design and behavioral topics. Target weaknesses. Keep answerable in 1-3 minutes. Return only JSON."""
    x=gemini_json(prompt,NEXT_SCHEMA); x.update(source="gemini",model=GEMINI_MODEL); return x

@app.post("/report")
def report(req:ReportRequest,request:Request):
    rate_limit(request)
    if not GEMINI_API_KEY: raise HTTPException(503,"AI report is not configured.")
    prompt=f"""You are the senior interviewer producing a final candidate report. Return ONLY JSON matching the schema.
Role: {req.role}
Job description: {req.job_description[:7000]}
Questions asked: {json.dumps(req.questions,ensure_ascii=False)[:6000]}
Per-question evaluation results: {json.dumps(req.results,ensure_ascii=False)[:12000]}
Base conclusions on supplied evaluations. Do not invent candidate facts. Readiness should reflect overall performance. Identify recurring weak dimensions and turn them into concrete role/JD-relevant revision topics. Make the action plan practical and ordered. Next questions should target weak areas. Be concise and honest."""
    x=gemini_json(prompt,REPORT_SCHEMA); x.update(source="gemini",model=GEMINI_MODEL); return x
