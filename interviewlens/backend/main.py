import os
import re
import sqlite3
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from research import search_web

# Vercel's deployment filesystem is read-only except for /tmp.
# This SQLite database is suitable only for the MVP; use a persistent
# database for durable community confirmations later.
DB=os.path.join('/tmp', 'interviewlens.db') if os.getenv('VERCEL') else 'interviewlens.db'

app=FastAPI(title='InterviewLens API')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

with db() as c:
    c.execute('CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY, role TEXT NOT NULL, question TEXT NOT NULL, confirmations INTEGER NOT NULL DEFAULT 0, UNIQUE(role,question))')
    c.execute('CREATE TABLE IF NOT EXISTS confirmations (id INTEGER PRIMARY KEY, question_id INTEGER NOT NULL, created_at TEXT NOT NULL)')

class PrepRequest(BaseModel): role:str; job_description:str=''
class ConfirmRequest(BaseModel): question_id:int
class ResearchRequest(BaseModel): role:str; company:str=''

SEED={'data analyst':['Explain INNER JOIN vs LEFT JOIN with an example.','How would you find duplicate records in SQL?','Walk me through a data analysis project you worked on.','How do you handle missing or inconsistent data?','What metrics would you use to measure business performance?','Write a SQL query to find the second-highest salary.'],'python developer':['What is the difference between a list, tuple, set and dictionary?','Explain decorators in Python.','What are generators and when would you use them?','How would you design a REST API for a simple service?','Explain exception handling and custom exceptions.','How do you optimize slow Python code?'],'software engineer':['Explain the time complexity of your solution.','How would you detect a cycle in a linked list?','What is the difference between a process and a thread?','Explain indexing in databases.','What happens when you enter a URL in a browser?','Design a URL shortener at a high level.']}

KEYWORD_QUESTIONS={
    'sql':['How would you use window functions to solve an analytical problem?','How would you optimize a slow SQL query?'],
    'python':['How do you test and debug Python code?','How would you improve the performance of a Python program?'],
    'pandas':['How would you use Pandas to clean and transform a dataset?','How do you handle missing values in Pandas?'],
    'power bi':['How would you design a Power BI dashboard for business stakeholders?','What is the difference between a measure and a calculated column in Power BI?'],
    'tableau':['How would you build an effective Tableau dashboard?','What is a Tableau calculated field and when would you use it?'],
    'excel':['How would you use PivotTables and lookup functions to analyze data?'],
    'statistics':['Which statistical methods would you use to compare two groups?','How would you explain statistical significance to a non-technical stakeholder?'],
    'machine learning':['How would you evaluate a machine learning model?','How would you handle overfitting in a machine learning model?'],
    'rest api':['How would you design and secure a REST API?'],
    'fastapi':['How would you structure a FastAPI application for production?'],
    'django':['How would you structure a Django application and its models?'],
    'aws':['How would you deploy and monitor an application on AWS?'],
    'azure':['How would you deploy and monitor an application on Azure?'],
    'docker':['Why would you use Docker and how would you containerize an application?'],
    'kubernetes':['What problem does Kubernetes solve and how would you deploy an application with it?'],
    'git':['How do you use Git to manage changes and resolve merge conflicts?'],
    'javascript':['What is the difference between var, let and const in JavaScript?'],
    'react':['How does React manage component state and rendering?'],
    'java':['What is the difference between an interface and an abstract class in Java?'],
    'c++':['What is the difference between a pointer and a reference in C++?'],
    'c#':['What is the difference between an interface and an abstract class in C#?'],
}

def role_key(role):
    r=role.lower()
    if 'analyst' in r:return 'data analyst'
    if 'python' in r:return 'python developer'
    return 'software engineer'

def jd_questions(job_description):
    text=(job_description or '').lower()
    found=[]
    for keyword,questions in KEYWORD_QUESTIONS.items():
        if re.search(r'(?<!\w)'+re.escape(keyword)+r'(?!\w)',text):
            found.extend(questions)
    return found

@app.get('/health')
def health(): return {'status':'ok'}

@app.post('/prep')
def prep(req:PrepRequest):
    role=req.role.strip() or 'Software Engineer'
    questions=[]
    seen=set()
    for q in SEED.get(role_key(role),SEED['software engineer']) + jd_questions(req.job_description):
        key=q.lower().strip()
        if key not in seen:
            seen.add(key); questions.append(q)
    questions=questions[:12]
    with db() as c:
        for q in questions:
            c.execute('INSERT OR IGNORE INTO questions(role,question) VALUES(?,?)',(role,q))
        rows=c.execute('SELECT id,question,confirmations FROM questions WHERE role=? ORDER BY confirmations DESC,id ASC',(role,)).fetchall()
    return {'role':role,'questions':[dict(r) for r in rows[:12]],'evidence_note':'Role and JD questions are recommendations unless a question has candidate confirmations.'}

@app.post('/research')
def research(req:ResearchRequest):
    if not req.role.strip(): raise HTTPException(400,'Role is required')
    return search_web(req.role.strip(),req.company.strip())

@app.post('/confirm')
def confirm(req:ConfirmRequest):
    with db() as c:
        if not c.execute('SELECT id FROM questions WHERE id=?',(req.question_id,)).fetchone(): raise HTTPException(404,'Question not found')
        c.execute('INSERT INTO confirmations(question_id,created_at) VALUES(?,?)',(req.question_id,datetime.utcnow().isoformat()))
        c.execute('UPDATE questions SET confirmations=confirmations+1 WHERE id=?',(req.question_id,))
        count=c.execute('SELECT confirmations FROM questions WHERE id=?',(req.question_id,)).fetchone()[0]
    return {'question_id':req.question_id,'confirmations':count}

@app.get('/questions/{role}')
def questions(role:str):
    with db() as c:
        rows=c.execute('SELECT id,question,confirmations FROM questions WHERE role=? ORDER BY confirmations DESC',(role,)).fetchall()
    return [dict(r) for r in rows]
