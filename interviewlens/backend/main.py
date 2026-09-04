import os
import sqlite3
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from research import search_web

# Vercel's deployment filesystem is read-only except for /tmp.
# This SQLite database is therefore suitable only for the MVP; use a
# persistent database for durable community confirmations later.
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

SEED={'data analyst':['Explain INNER JOIN vs LEFT JOIN with an example.','How would you find duplicate records in SQL?','How do you handle missing or inconsistent data?','What metrics would you use to measure business performance?','Write a SQL query to find the second-highest salary.'],'python developer':['What is the difference between a list, tuple, set and dictionary?','Explain decorators in Python.','What are generators and when would you use them?','How would you design a REST API for a simple service?','How do you optimize slow Python code?'],'software engineer':['Explain the time complexity of your solution.','How would you detect a cycle in a linked list?','What is the difference between a process and a thread?','Explain indexing in databases.','What happens when you enter a URL in a browser?']}

def role_key(role):
    r=role.lower()
    if 'analyst' in r:return 'data analyst'
    if 'python' in r:return 'python developer'
    return 'software engineer'

@app.get('/health')
def health(): return {'status':'ok'}

@app.post('/prep')
def prep(req:PrepRequest):
    role=req.role.strip() or 'Software Engineer'; questions=SEED.get(role_key(role),SEED['software engineer'])
    with db() as c:
        for q in questions:c.execute('INSERT OR IGNORE INTO questions(role,question) VALUES(?,?)',(role,q))
        rows=c.execute('SELECT id,question,confirmations FROM questions WHERE role=?',(role,)).fetchall()
    return {'role':role,'questions':[dict(r) for r in rows],'evidence_note':'Role recommendations are not presented as verified interview reports.'}

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
    with db() as c: rows=c.execute('SELECT id,question,confirmations FROM questions WHERE role=? ORDER BY confirmations DESC',(role,)).fetchall()
    return [dict(r) for r in rows]
