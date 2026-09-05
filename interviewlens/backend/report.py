import json, os, time
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
KEY=os.getenv('GEMINI_API_KEY',''); MODEL=os.getenv('GEMINI_MODEL','gemini-2.5-flash')
app=FastAPI(title='InterviewLens Final Report')
app.add_middleware(CORSMiddleware,allow_origins=['https://karanaldo-07.github.io','http://localhost:3000','http://127.0.0.1:5500'],allow_methods=['POST','OPTIONS'],allow_headers=['Content-Type'])
H={}
def limit(r):
 ip=(r.headers.get('x-forwarded-for') or r.client.host or 'unknown').split(',')[0].strip(); now=time.time(); H[ip]=[x for x in H.get(ip,[]) if now-x<600]
 if len(H[ip])>=12: raise HTTPException(429,'Too many AI requests. Please try again later.')
 H[ip].append(now)
class Req(BaseModel):
 role:str=Field(default='Software Engineer',max_length=120); job_description:str=Field(default='',max_length=12000); results:list[dict]=Field(min_length=1,max_length=10); questions:list[str]=Field(default_factory=list,max_length=10)
SCHEMA={'type':'object','properties':{'readiness':{'type':'string','enum':['Not ready yet','Developing','Interview-ready','Strongly interview-ready']},'headline':{'type':'string','maxLength':180},'summary':{'type':'string','maxLength':700},'strengths':{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':5},'weak_areas':{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':5},'priority_topics':{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':6},'action_plan':{'type':'array','items':{'type':'string'},'minItems':3,'maxItems':6},'next_questions':{'type':'array','items':{'type':'string'},'minItems':3,'maxItems':5}},'required':['readiness','headline','summary','strengths','weak_areas','priority_topics','action_plan','next_questions']}
def call(p):
 try:
  r=requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent',headers={'x-goog-api-key':KEY,'Content-Type':'application/json'},json={'contents':[{'parts':[{'text':p}]}],'generationConfig':{'temperature':0.2,'responseMimeType':'application/json','responseSchema':SCHEMA}},timeout=25); r.raise_for_status(); return json.loads(r.json()['candidates'][0]['content']['parts'][0]['text'])
 except Exception as e: raise HTTPException(502,f'AI request failed: {type(e).__name__}')
@app.post('/')
@app.post('/report')
@app.post('/mock/report')
def report(req:Req,request:Request):
 limit(request)
 if not KEY: raise HTTPException(503,'AI report is not configured.')
 p=f'''You are the senior interviewer producing a final candidate report. Return ONLY JSON matching the schema.
Role: {req.role}
Job description: {req.job_description[:7000]}
Questions asked: {json.dumps(req.questions,ensure_ascii=False)[:6000]}
Per-question evaluation results: {json.dumps(req.results,ensure_ascii=False)[:12000]}
Base conclusions on supplied evaluations. Do not invent candidate facts. Readiness should reflect overall performance. Identify recurring weak dimensions and turn them into concrete role/JD-relevant revision topics. Make the action plan practical and ordered. Next questions should target weak areas. Be concise and honest.'''
 x=call(p); x.update(source='gemini',model=MODEL); return x
