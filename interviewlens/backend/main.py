import hashlib
import os
import re
import sqlite3
import time
from datetime import datetime

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from research import search_web

DB=os.path.join('/tmp','interviewlens.db') if os.getenv('VERCEL') else 'interviewlens.db'
SUPABASE_URL=os.getenv('SUPABASE_URL','').rstrip('/')
SUPABASE_KEY=os.getenv('SUPABASE_SERVICE_ROLE_KEY','')
CONFIRM_SALT=os.getenv('INTERVIEWLENS_CONFIRM_SALT','change-this-salt')

app=FastAPI(title='InterviewLens API')
app.add_middleware(CORSMiddleware,allow_origins=['https://karanaldo-07.github.io','http://localhost:3000','http://127.0.0.1:5500'],allow_methods=['GET','POST','OPTIONS'],allow_headers=['Content-Type'])

_RATE={}
def rate_limit(request:Request,bucket:str,limit:int,window:int):
    ip=(request.headers.get('x-forwarded-for') or request.client.host or 'unknown').split(',')[0].strip()
    key=f'{bucket}:{ip}'; now=time.time()
    hits=[t for t in _RATE.get(key,[]) if now-t<window]
    if len(hits)>=limit: raise HTTPException(429,'Too many requests. Please try again later.')
    hits.append(now); _RATE[key]=hits
    if len(_RATE)>2000:
        for k in list(_RATE)[:500]: _RATE.pop(k,None)

def sqlite_db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

with sqlite_db() as c:
    c.execute('CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY, role TEXT NOT NULL, question TEXT NOT NULL, confirmations INTEGER NOT NULL DEFAULT 0, UNIQUE(role,question))')
    c.execute('CREATE TABLE IF NOT EXISTS confirmations (id INTEGER PRIMARY KEY, question_id INTEGER NOT NULL, fingerprint TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(question_id,fingerprint))')

def persistent_enabled(): return bool(SUPABASE_URL and SUPABASE_KEY)

def sb_request(method,path,params=None,json_body=None,prefer='return=representation'):
    r=requests.request(method,f'{SUPABASE_URL}/rest/v1/{path}',headers={'apikey':SUPABASE_KEY,'Authorization':f'Bearer {SUPABASE_KEY}','Content-Type':'application/json','Prefer':prefer},params=params,json=json_body,timeout=10)
    r.raise_for_status(); return r.json() if r.text else None

def question_rows(role):
    if persistent_enabled():
        try:
            return sb_request('GET','questions',params={'select':'id,question,confirmations','role':f'eq.{role}','order':'confirmations.desc,id.asc','limit':'12'}) or []
        except requests.RequestException: pass
    with sqlite_db() as c:
        return [dict(r) for r in c.execute('SELECT id,question,confirmations FROM questions WHERE role=? ORDER BY confirmations DESC,id ASC LIMIT 12',(role,)).fetchall()]

def seed_questions(role,questions):
    if persistent_enabled():
        try:
            sb_request('POST','questions',params={'on_conflict':'role,question'},json_body=[{'role':role,'question':q} for q in questions],prefer='resolution=ignore-duplicates,return=minimal'); return
        except requests.RequestException: pass
    with sqlite_db() as c:
        for q in questions: c.execute('INSERT OR IGNORE INTO questions(role,question) VALUES(?,?)',(role,q))

class PrepRequest(BaseModel): role:str; job_description:str=''
class ConfirmRequest(BaseModel): question_id:int
class ResearchRequest(BaseModel): role:str; company:str=''

SEED={'data analyst':['Explain INNER JOIN vs LEFT JOIN with an example.','How would you find duplicate records in SQL?','Walk me through a data analysis project you worked on.','How do you handle missing or inconsistent data?','What metrics would you use to measure business performance?','Write a SQL query to find the second-highest salary.'],'python developer':['What is the difference between a list, tuple, set and dictionary?','Explain decorators in Python.','What are generators and when would you use them?','How would you design a REST API for a simple service?','Explain exception handling and custom exceptions.','How do you optimize slow Python code?'],'software engineer':['Explain the time complexity of your solution.','How would you detect a cycle in a linked list?','What is the difference between a process and a thread?','Explain indexing in databases.','What happens when you enter a URL in a browser?','Design a URL shortener at a high level.']}
KEYWORD_QUESTIONS={'sql':['How would you use window functions to solve an analytical problem?','How would you optimize a slow SQL query?'],'python':['How do you test and debug Python code?','How would you improve the performance of a Python program?'],'pandas':['How would you use Pandas to clean and transform a dataset?','How do you handle missing values in Pandas?'],'power bi':['How would you design a Power BI dashboard for business stakeholders?','What is the difference between a measure and a calculated column in Power BI?'],'tableau':['How would you build an effective Tableau dashboard?','What is a Tableau calculated field and when would you use it?'],'excel':['How would you use PivotTables and lookup functions to analyze data?'],'statistics':['Which statistical methods would you use to compare two groups?','How would you explain statistical significance to a non-technical stakeholder?'],'machine learning':['How would you evaluate a machine learning model?','How would you handle overfitting in a machine learning model?'],'rest api':['How would you design and secure a REST API?'],'fastapi':['How would you structure a FastAPI application for production?'],'django':['How would you structure a Django application and its models?'],'aws':['How would you deploy and monitor an application on AWS?'],'azure':['How would you deploy and monitor an application on Azure?'],'docker':['Why would you use Docker and how would you containerize an application?'],'kubernetes':['What problem does Kubernetes solve and how would you deploy an application with it?'],'git':['How do you use Git to manage changes and resolve merge conflicts?'],'javascript':['What is the difference between var, let and const in JavaScript?'],'react':['How does React manage component state and rendering?'],'java':['What is the difference between an interface and an abstract class in Java?'],'c++':['What is the difference between a pointer and a reference in C++?'],'c#':['What is the difference between an interface and an abstract class in C#?']}

def role_key(role):
    r=role.lower()
    if 'analyst' in r:return 'data analyst'
    if 'python' in r:return 'python developer'
    return 'software engineer'

def jd_questions(job_description):
    text=(job_description or '').lower(); found=[]
    for keyword,questions in KEYWORD_QUESTIONS.items():
        if re.search(r'(?<!\w)'+re.escape(keyword)+r'(?!\w)',text): found.extend(questions)
    return found

@app.get('/health')
def health(): return {'status':'ok','database':'supabase' if persistent_enabled() else 'sqlite-mvp'}

@app.post('/prep')
def prep(req:PrepRequest,request:Request):
    rate_limit(request,'prep',30,300)
    role=req.role.strip() or 'Software Engineer'; questions=[]; seen=set()
    for q in SEED.get(role_key(role),SEED['software engineer'])+jd_questions(req.job_description):
        key=q.lower().strip()
        if key not in seen: seen.add(key); questions.append(q)
    seed_questions(role,questions[:12]); rows=question_rows(role)
    return {'role':role,'questions':rows,'evidence_note':'Role and JD questions are recommendations unless a question has candidate confirmations.','database':'persistent' if persistent_enabled() else 'mvp'}

@app.post('/research')
def research(req:ResearchRequest,request:Request):
    rate_limit(request,'research',10,600)
    if not req.role.strip(): raise HTTPException(400,'Role is required')
    return search_web(req.role.strip(),req.company.strip())

@app.post('/confirm')
def confirm(req:ConfirmRequest,request:Request):
    rate_limit(request,'confirm',20,600)
    ip=(request.headers.get('x-forwarded-for') or request.client.host or 'unknown').split(',')[0].strip(); ua=request.headers.get('user-agent','')
    fingerprint=hashlib.sha256(f'{CONFIRM_SALT}|{ip}|{ua}'.encode()).hexdigest()
    if persistent_enabled():
        try:
            result=sb_request('POST','rpc/confirm_question',json_body={'p_question_id':req.question_id,'p_fingerprint':fingerprint})
            count=result[0] if isinstance(result,list) else result
            return {'question_id':req.question_id,'confirmations':int(count),'persistent':True}
        except requests.RequestException as exc:
            if getattr(exc.response,'status_code',None)==404: raise HTTPException(404,'Question not found')
    with sqlite_db() as c:
        if not c.execute('SELECT id FROM questions WHERE id=?',(req.question_id,)).fetchone(): raise HTTPException(404,'Question not found')
        inserted=c.execute('INSERT OR IGNORE INTO confirmations(question_id,fingerprint,created_at) VALUES(?,?,?)',(req.question_id,fingerprint,datetime.utcnow().isoformat())).rowcount
        if inserted: c.execute('UPDATE questions SET confirmations=confirmations+1 WHERE id=?',(req.question_id,))
        count=c.execute('SELECT confirmations FROM questions WHERE id=?',(req.question_id,)).fetchone()[0]
    return {'question_id':req.question_id,'confirmations':count,'persistent':False}

@app.get('/questions/{role}')
def questions(role:str): return question_rows(role)
