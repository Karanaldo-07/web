const $=id=>document.getElementById(id);
const role=$('role'),jd=$('jd'),company=$('company'),results=$('results');
const API=window.INTERVIEWLENS_API||'';

const packs={
  'data analyst':{topics:['SQL: joins, GROUP BY, window functions','Excel: lookups, pivots, cleaning','Python/Pandas basics','Statistics and probability','Power BI/Tableau and dashboard design'],behavioral:['Tell me about yourself.','Describe a project where you used data to solve a problem.','Tell me about a time your analysis changed a decision.','How do you handle ambiguous requirements?'],checklist:['Research the company and its product','Review every technology named in the JD','Prepare 2 project stories with measurable results','Practice SQL hands-on problems','Prepare 3 questions for the interviewer'],questions:['Explain INNER JOIN vs LEFT JOIN with an example.','How would you find duplicate records in SQL?','Walk me through a data analysis project you worked on.','How do you handle missing or inconsistent data?','What metrics would you use to measure business performance?','Write a SQL query to find the second-highest salary.']},
  'python developer':{topics:['Python data structures and OOP','Decorators, generators and iterators','REST APIs and HTTP','SQL and database design','Testing, Git and debugging','FastAPI/Django/Flask basics'],behavioral:['Tell me about yourself.','Explain your most challenging project.','How do you debug a production issue?','Tell me about a technical disagreement and how you resolved it.'],checklist:['Revise your projects line by line','Practice Python coding without autocomplete','Review API status codes and authentication','Prepare one debugging story','Research the company engineering stack'],questions:['What is the difference between a list, tuple, set and dictionary?','Explain decorators in Python.','What are generators and when would you use them?','How would you design a REST API for a simple service?','Explain exception handling and custom exceptions.','How do you optimize slow Python code?']},
  'software engineer':{topics:['DSA: arrays, strings, hash maps, trees','OOP and design principles','DBMS and SQL','Operating systems basics','Networking and HTTP','System design fundamentals','Git and testing'],behavioral:['Tell me about yourself.','Describe your most impactful project.','Tell me about a bug that was difficult to solve.','Why do you want to work here?'],checklist:['Practice 5–10 coding problems','Know your resume projects deeply','Revise SQL and OOP','Review the company product and tech stack','Prepare thoughtful interviewer questions'],questions:['Explain the time complexity of your solution.','How would you detect a cycle in a linked list?','What is the difference between a process and a thread?','Explain indexing in databases.','What happens when you enter a URL in a browser?','Design a URL shortener at a high level.']}
};

function choosePack(text){const t=text.toLowerCase();if(t.includes('data analyst')||t.includes('analyst'))return packs['data analyst'];if(t.includes('python'))return packs['python developer'];return packs['software engineer']}
function renderList(id,items){$(id).innerHTML=items.map(x=>`<li>${escapeHtml(x)}</li>`).join('')}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}

function answerGuide(q){
  const t=q.toLowerCase();
  if(t.includes('sql')||t.includes('join')||t.includes('query')||t.includes('database'))return 'Answer with the concept, a small example/query, edge cases, and explain why your approach works.';
  if(t.includes('python')||t.includes('decorator')||t.includes('generator'))return 'Define it clearly, show a short example, explain when you would use it, and mention one practical trade-off.';
  if(t.includes('time complexity')||t.includes('cycle')||t.includes('algorithm'))return 'State the approach first, walk through the key steps, then give time and space complexity and test an edge case.';
  if(t.includes('project')||t.includes('tell me')||t.includes('why do you'))return 'Use STAR: Situation, Task, Action, Result. Keep the story specific and include measurable impact where possible.';
  if(t.includes('design')||t.includes('system'))return 'Clarify requirements, propose a simple architecture, discuss data flow and trade-offs, then cover scale, reliability, and failure cases.';
  return 'Start with a concise definition, give a concrete example from your work or study, explain your reasoning, and finish with a practical takeaway.'
}

function renderResearch(data){
  const status=$('researchStatus'),leads=$('researchLeads'),sources=$('sources');
  if(!API){status.textContent='Connect API to enable';leads.innerHTML='<div class="research-empty">Live web research will appear here after the backend is deployed and connected.</div>';sources.innerHTML='';return}
  if(!data||!data.enabled){status.textContent='Waiting for API key';leads.innerHTML=`<div class="research-empty">${escapeHtml(data?.message||'Web research is not available yet.')}</div>`;sources.innerHTML='';return}
  status.textContent=`${data.sources?.length||0} sources found`;
  const ql=data.question_leads||[];
  leads.innerHTML=ql.length?ql.map(x=>`<div class="lead-item"><p>${escapeHtml(x.question)}</p><small>Research lead · <a href="${escapeHtml(x.source_url)}" target="_blank" rel="noopener noreferrer">View source</a></small></div>`).join(''):'<div class="research-empty">No clean question leads were extracted. Check the sources below for interview reports.</div>';
  sources.innerHTML=(data.sources||[]).slice(0,10).map(x=>`<div class="source"><a href="${escapeHtml(x.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(x.title||x.url)}</a><small>${escapeHtml(x.snippet||'')}</small></div>`).join('')
}

async function generate(){
  const r=(role.value||'Software Engineer').trim();
  const c=(company?.value||'').trim();
  $('resultTitle').textContent=r;
  $('resultSub').textContent=jd.value.trim()?(c?`Customized from your job description, role patterns, and ${c} web research.`:'Customized from your job description + role patterns.'):(c?`Role-based preparation with ${c} web research.`:'Role-based preparation pack.');
  let data=null;
  if(API){try{const res=await fetch(API+'/prep',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({role:r,job_description:jd.value})});if(res.ok)data=await res.json()}catch(e){console.warn('InterviewLens API unavailable; using local pack.')}}
  const p=choosePack(r+' '+jd.value);
  renderQuestions((data&&data.questions?.length)?data.questions.map(x=>({id:x.id,q:x.question,count:x.confirmations})):p.questions.map(q=>({q,count:0})));
  renderList('topics',p.topics);renderList('behavioral',p.behavioral);renderList('checklist',p.checklist);
  results.classList.remove('hidden');renderResearch(null);
  if(API){try{const res=await fetch(API+'/research',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({role:r,company:c})});if(res.ok)renderResearch(await res.json());else renderResearch({enabled:false,message:'Research request failed.'})}catch(e){renderResearch({enabled:false,message:'Could not reach the research backend.'})}}
  results.scrollIntoView({behavior:'smooth'})
}

async function confirm(id,q,button,items){
  if(button.dataset.confirmed==='1')return;
  if(API&&id){
    try{
      const res=await fetch(API+'/confirm',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question_id:id})});
      if(res.ok){
        const d=await res.json();
        const countEl=button.parentElement.querySelector('small b');
        if(countEl)countEl.textContent=d.confirmations;
        button.classList.add('confirmed');button.textContent='✓ Asked in an interview';button.dataset.confirmed='1';
        localStorage.setItem('confirmed:'+id,'1');
        const item=items.find(x=>x.id===id);if(item)item.count=d.confirmations;
        updateSignal(items);
        return
      }
    }catch(e){console.warn('Community confirmation failed; using local fallback.')}}
  const k='asked:'+q.toLowerCase().replace(/\W+/g,'-');
  if(localStorage.getItem(k))return;
  localStorage.setItem(k,'1');button.classList.add('confirmed');button.textContent='✓ Asked in an interview';button.dataset.confirmed='1';
  const countEl=button.parentElement.querySelector('small b');if(countEl)countEl.textContent='1';
  updateSignal(items)
}

function renderQuestions(items){
  $('questions').innerHTML=items.map((x,i)=>{
    const q=x.q||x,n=Number(x.count)||0,already=x.id&&localStorage.getItem('confirmed:'+x.id);
    return `<div class="q"><div class="q-head"><span class="q-num">${String(i+1).padStart(2,'0')}</span><p>${escapeHtml(q)}</p></div><small>${x.id?'Community reports':'Recommended for this role'} · Confirmations: <b>${n}</b></small><details class="answer"><summary>How should I answer?</summary><p>${escapeHtml(answerGuide(q))}</p></details><button class="asked ${already?'confirmed':''}" data-id="${x.id||''}" data-confirmed="${already?'1':'0'}">${already?'✓ Asked in an interview':'I was asked this'}</button></div>`
  }).join('');
  const buttons=[...document.querySelectorAll('.asked')];
  buttons.forEach((b,i)=>{const item=items[i],q=item.q||item;b.onclick=()=>confirm(item.id,q,b,items)});
  updateSignal(items)
}

function updateSignal(items=[]){
  const communityTotal=items.reduce((sum,item)=>sum+(Number(item.count)||0),0);
  const localTotal=new Set([...Object.keys(localStorage).filter(k=>k.startsWith('asked:')), ...Object.keys(localStorage).filter(k=>k.startsWith('confirmed:'))]).size;
  $('signalNumber').textContent=communityTotal;
  $('confidence').textContent=communityTotal?`${communityTotal} candidate confirmation${communityTotal===1?'':'s'} across these questions`:'Community confidence: building';
  const localLabel=$('confidence');
  if(localLabel&&localTotal&&communityTotal===0)localLabel.textContent=`Your confirmation is recorded locally while this pack builds community evidence`;
}

$('generate').onclick=generate;
$('reset').onclick=()=>{results.classList.add('hidden');role.focus();window.scrollTo({top:0,behavior:'smooth'})};
document.querySelectorAll('.examples button').forEach(b=>b.onclick=()=>{role.value=b.dataset.role;role.focus()});
updateSignal();