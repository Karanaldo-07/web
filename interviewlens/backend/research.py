import os
import re
import requests

TAVILY_URL='https://api.tavily.com/search'

QUESTION_PATTERNS=(
    re.compile(r'(?i)(?:asked|ask|question|questions|interviewers? asked)[^?]{0,180}\?'),
    re.compile(r'(?i)(?:^|[.!]\s+)(?:what|why|how|when|where|which|explain|describe|tell me|walk me through|write)\b[^?]{8,180}\?'),
)


def _clean_question(text):
    text=re.sub(r'<[^>]+>', ' ', text or '')
    text=re.sub(r'\s+', ' ', text).strip(' .-–—')
    if not text.endswith('?'):
        text += '?'
    return text


def extract_question_leads(sources):
    """Extract cautious question leads from search snippets.

    These are research leads, not verified interview reports. A later version can
    fetch permitted page content and use stronger evidence classification.
    """
    leads=[]
    seen=set()
    for source in sources:
        text=f"{source.get('title','')} {source.get('snippet','')}"
        candidates=[]
        for pattern in QUESTION_PATTERNS:
            candidates.extend(pattern.findall(text))
        for raw in candidates:
            q=_clean_question(raw)
            key=re.sub(r'[^a-z0-9]+',' ',q.lower()).strip()
            if len(key)<15 or key in seen or len(q)>220:
                continue
            if any(skip in key for skip in ('interview experience','interview questions','questions asked in interview')):
                continue
            seen.add(key)
            leads.append({'question':q,'evidence_type':'research_lead','source_url':source.get('url',''),'source_title':source.get('title','')})
    return leads[:20]


def search_web(role: str, company: str = ''):
    key=os.getenv('TAVILY_API_KEY')
    if not key:
        return {'enabled':False,'message':'Web research is ready but TAVILY_API_KEY is not configured.','sources':[],'question_leads':[]}

    base=f'"{role}" interview questions'
    queries=[base, f'"{role}" interview experience', f'"{role}" technical interview questions']
    if company:
        queries=[f'"{company}" "{role}" interview questions',f'"{company}" "{role}" interview experience',f'"{company}" "{role}" interview']

    sources=[]
    headers={
        'Content-Type':'application/json',
        'Authorization':f'Bearer {key}',
    }

    for q in queries:
        try:
            r=requests.post(
                TAVILY_URL,
                json={
                    'query':q,
                    'search_depth':'basic',
                    'topic':'general',
                    'max_results':10,
                    'country':'india',
                    'include_answer':False,
                    'include_raw_content':False,
                },
                headers=headers,
                timeout=15,
            )
            r.raise_for_status()
            for item in r.json().get('results',[]):
                url=item.get('url')
                if url and not any(s['url']==url for s in sources):
                    sources.append({
                        'title':item.get('title',''),
                        'url':url,
                        'snippet':item.get('content',''),
                        'query':q,
                    })
        except requests.RequestException:
            continue

    return {
        'enabled':True,
        'queries':queries,
        'sources':sources[:20],
        'question_leads':extract_question_leads(sources),
    }
