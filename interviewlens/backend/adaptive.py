import json, os, time
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

KEY=os.getenv('GEMINI_API_KEY',''); MODEL=os.getenv('GEMINI_MODEL','gemini-3.5-flash')
MODELS=list(dict.fromkeys([m for m in [MODEL,'gemini-3.5-flash','gemini-3.5-flash-lite'] if m]))
app=FastAPI(title='InterviewLens Adaptive Interviewer')
app.add_middleware(CORSMiddleware,allow_origins=['https://karanaldo-07.github.io','http://localhost:3000','http://127.0.0.1:5500'],allow_methods=['POST','OPTIONS'],allow_headers=['Content-Type'])
H={}
def limit(r):
 ip=(r.headers.get('x-forwarded-for') or r.client.host or 'unknown').split(',')[0].strip(); now=time.time(); H[ip]=[x for x in H.get(ip,[]) if now-x<600]
 if len(H[ip])>=12: raise HTTPException(429,'Too many AI requests. Please try again later.')
 H[ip].append(now)
class Req(BaseModel):
 role:str=Field(default='Software Engineer',max_length=120); job_description:str=Field(default='',max_length=12000); current_question:str=Field(min_length=3,max_length=1000); candidate_answer:str=Field(min_length=5,max_length=12000); evaluation:dict; asked_questions:list[str]=Field(default_factory=list,max_length=10); question_number:int=Field(default=1,ge=1,le=10); total_questions:int=Field(default=5,ge=1,le=10)
SCHEMA={'type':'object','properties':{'next_question':{'type':'string','minLength':5,'maxLength':1000},'category':{'type':'string','enum':['Technical','Coding','System Design','Behavioral','Problem Solving','Role-specific']},'difficulty':{'type':'string','enum':['Easy','Medium','Hard']},'reason':{'type':'string','maxLength':500}},'required':['next_question','category','difficulty','reason']}
def call(p):
 last=None
 for model in MODELS:
  try:
   r=requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',headers={'x-goog-api-key':KEY,'Content-Type':'application/json'},json={'contents':[{'parts':[{'text':p}]}],'generationConfig':{'temperature':0.2,'responseMimeType':'application/json','responseSchema':SCHEMA}},timeout=25); r.raise_for_status(); return json.loads(r.json()['candidates'][0]['content']['parts'][0]['text']),model
  except Exception as e:
   last=getattr(getattr(e,'response',None),'status_code',None)
 raise HTTPException(502,f'AI request failed after model fallback (last_status={last})')
@app.post('/')
@app.post('/next')
@app.post('/mock/next')
def next_question(req:Req,request:Request):
 limit(request)
 if not KEY: raise HTTPException(503,'AI interviewer is not configured.')
 asked='\n'.join('- '+q for q in req.asked_questions[-10:]) or '- none'
 p=f'''You are the adaptive interviewer in a realistic {req.role} interview. Generate exactly one next interview question as JSON.
Role: {req.role}
Job description: {req.job_description[:7000]}
Current question: {req.current_question}
Candidate answer: {req.candidate_answer[:7000]}
Evaluation: {json.dumps(req.evaluation,ensure_ascii=False)[:4000]}
Questions already asked:\n{asked}
This is question {req.question_number} of {req.total_questions}.
Adapt difficulty: strong answers get a deeper follow-up or harder adjacent topic; weak answers get a focused clarifying question or simpler foundation check. Never repeat. Stay role/JD relevant. Mix technical, coding/problem-solving, system-design and behavioral topics. Target weaknesses. Keep answerable in 1-3 minutes. Return only JSON.'''
 x,used_model=call(p); x.update(source='gemini',model=used_model); return x
