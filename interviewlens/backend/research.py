import os
import requests
from urllib.parse import quote_plus

BRAVE_URL='https://api.search.brave.com/res/v1/web/search'

def search_web(role: str, company: str = ''):
    key=os.getenv('BRAVE_SEARCH_API_KEY')
    if not key:
        return {'enabled':False,'message':'Web research is ready but BRAVE_SEARCH_API_KEY is not configured.','sources':[]}
    base=f'"{role}" interview questions'
    queries=[base, f'"{role}" interview experience', f'"{role}" technical interview questions']
    if company:
        queries=[f'"{company}" "{role}" interview questions',f'"{company}" "{role}" interview experience',f'"{company}" "{role}" interview']
    sources=[]
    for q in queries:
        try:
            r=requests.get(BRAVE_URL,params={'q':q,'count':10,'country':'IN','search_lang':'en','safesearch':'moderate'},headers={'Accept':'application/json','X-Subscription-Token':key},timeout=10)
            r.raise_for_status()
            for item in r.json().get('web',{}).get('results',[]):
                url=item.get('url');
                if url and not any(s['url']==url for s in sources):
                    sources.append({'title':item.get('title',''),'url':url,'snippet':item.get('description',''),'query':q})
        except requests.RequestException:
            continue
    return {'enabled':True,'queries':queries,'sources':sources[:20]}
