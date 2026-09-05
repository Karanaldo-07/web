const $=id=>document.getElementById(id);
const role=$('role'),jd=$('jd'),company=$('company'),results=$('results');
const API=window.INTERVIEWLENS_API||'';
let currentRole='Software Engineer';
let currentQuestions=[];
let reportQuestion=null;

const packs={
  'data analyst':{topics:['SQL: joins, GROUP BY, window functions','Excel: lookups, pivots, cleaning','Python/Pandas basics','Statistics and probability','Power BI/Tableau and dashboard design'],behavioral:['Tell me about yourself.','Describe a project where you used data to solve a problem.','Tell me about a time your analysis changed a decision.','How do you handle ambiguous requirements?'],checklist:['Research the company and its product','Review every technology named in the JD','Prepare 2 project stories with measurable results','Practice SQL hands-on problems','Prepare 3 questions for the interviewer']},
  'python developer':{topics:['Python data structures and OOP','Decorators, generators and iterators','REST APIs and HTTP','SQL and database design','Testing, Git and debugging','FastAPI/Django/Flask basics'],behavioral:['Tell me about yourself.','Explain your most challenging project.','How do you debug a production issue?','Tell me about a technical disagreement and how you resolved it.'],checklist:['Revise your projects line by line','Practice Python coding without autocomplete','Review API status codes and authentication','Prepare one debugging story','Research the company engineering stack']},
  'frontend developer':{topics:['HTML, CSS and responsive design','JavaScript fundamentals','React/components/state if listed','Browser rendering and performance','Accessibility and testing','Git and API integration'],behavioral:['Tell me about yourself.','Describe a frontend project you are proud of.','How did you improve a page or application’s performance?','Tell me about a difficult product requirement.'],checklist:['Know your frontend projects line by line','Practice JavaScript fundamentals','Review browser/network debugging','Prepare one performance example','Research the company product and frontend stack']},
  'backend developer':{topics:['REST APIs and HTTP','Databases, SQL and indexing','Authentication and authorization','Caching, queues and reliability','Testing and observability','Cloud deployment and scaling'],behavioral:['Tell me about yourself.','Describe a backend system you built.','Tell me about a production issue you solved.','How do you handle changing requirements?'],checklist:['Know your API and database choices','Practice SQL and API design','Review authentication and error handling','Prepare one production-debugging story','Research the company backend stack']},
  'full stack developer':{topics:['Frontend fundamentals','Backend/API design','SQL and data modeling','Authentication and security','Testing and debugging','Deployment and cloud basics'],behavioral:['Tell me about yourself.','Walk me through a full-stack project.','How did you debug an issue across frontend and backend?','How do you balance speed and code quality?'],checklist:['Trace one project from UI to database','Review API contracts and error handling','Practice debugging with browser/network tools','Prepare one end-to-end project story','Research the company product and stack']},
  'data scientist':{topics:['Python, Pandas and data cleaning','Statistics and probability','Machine learning fundamentals','Model evaluation and validation','Feature engineering and overfitting','Communicating results to stakeholders'],behavioral:['Tell me about yourself.','Walk me through a machine learning project.','How did your model influence a decision?','Tell me about a model that did not work and what you changed.'],checklist:['Know your models and metrics deeply','Practice explaining trade-offs simply','Review validation and leakage','Prepare one measurable project outcome','Research the company’s data products']},
  'devops engineer':{topics:['Linux and networking','Git and CI/CD','Docker and Kubernetes','Cloud infrastructure','Monitoring and observability','Reliability and incident response'],behavioral:['Tell me about yourself.','Describe a deployment or reliability problem you solved.','Tell me about an outage you handled.','How do you balance delivery speed with reliability?'],checklist:['Review one deployment pipeline end to end','Practice troubleshooting scenarios','Know your cloud and container choices','Prepare one incident story','Research the company infrastructure stack']},
  'qa engineer':{topics:['Test strategy and test cases','Unit, integration and end-to-end testing','API testing','Automation frameworks','Defect investigation','CI/CD and regression testing'],behavioral:['Tell me about yourself.','Describe a difficult defect you found.','How do you decide what to automate?','Tell me about a disagreement over defect priority.'],checklist:['Review testing terminology','Practice writing test cases','Prepare an API testing example','Know your automation framework','Research the company release process']},
  'software engineer':{topics:['DSA: arrays, strings, hash maps, trees','OOP and design principles','DBMS and SQL','Operating systems basics','Networking and HTTP','System design fundamentals','Git and testing'],behavioral:['Tell me about yourself.','Describe your most impactful project.','Tell me about a bug that was difficult to solve.','Why do you want to work here?'],checklist:['Practice 5–10 coding problems','Know your resume projects deeply','Revise SQL and OOP','Review the company product and tech stack','Prepare thoughtful interviewer questions']}
};

function choosePack(text){
  const t=text.toLowerCase();
  if(t.includes('data analyst')||t.includes('business analyst')||t.includes('analyst'))return packs['data analyst'];
  if(t.includes('data scientist')||t.includes('machine learning')||t.includes('ml engineer'))return packs['data scientist'];
  if(t.includes('devops')||t.includes('site reliability')||t.includes('sre'))return packs['devops engineer'];
  if(t.includes('qa')||t.includes('quality assurance')||t.includes('tester'))return packs['qa engineer'];
  if(t.includes('full stack')||t.includes('fullstack'))return packs['full stack developer'];
  if(t.includes('frontend')||t.includes('front end')||t.includes('ui developer'))return packs['frontend developer'];
  if(t.includes('backend')||t.includes('back end'))return packs['backend developer'];
  if(t.includes('python'))return packs['python developer'];
  return packs['software engineer']
}
function renderList(id,items){$(id).innerHTML=items.map(x=>`<li>${escapeHtml(x)}</li>`).join('')}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}

function answerGuide(q,jdKeywords=[]){
  const t=q.toLowerCase(), context=jdKeywords.length?` Tie your answer directly to the JD focus: ${jdKeywords.join(', ')}.`:'';
  if(t.includes('sql')||t.includes('join')||t.includes('query')||t.includes('database'))return 'Start with the concept, then write or describe a small query/example. Explain edge cases, performance, and why your approach fits the data.'+context;
  if(t.includes('python')||t.includes('decorator')||t.includes('generator'))return 'Define the Python concept, show a compact example, explain when you would use it, and mention a practical trade-off such as readability, memory, or performance.'+context;
  if(t.includes('pandas'))return 'Explain the transformation step by step, name the Pandas operations you would use, and discuss missing values, data types, validation, and performance on larger datasets.'+context;
  if(t.includes('power bi')||t.includes('tableau')||t.includes('dashboard'))return 'Start from the stakeholder question, explain the data/model, choose a few useful metrics and visuals, and describe how you would validate that the dashboard leads to the right decision.'+context;
  if(t.includes('machine learning')||t.includes('model')||t.includes('overfitting'))return 'Frame the business problem first, explain the baseline and evaluation metric, describe validation and leakage risks, then discuss model choice, errors, and how you would improve it.'+context;
  if(t.includes('api')||t.includes('rest')||t.includes('fastapi')||t.includes('django'))return 'Cover the endpoint contract, validation, authentication/authorization, error handling, database interaction, testing, and observability. Explain the trade-offs behind your design.'+context;
  if(t.includes('docker')||t.includes('kubernetes')||t.includes('deploy')||t.includes('deployment')||t.includes('ci/cd'))return 'Explain the deployment path from code to production, configuration/secrets, health checks, rollback strategy, monitoring, and how you would minimize deployment risk.'+context;
  if(t.includes('react')||t.includes('javascript')||t.includes('frontend')||t.includes('browser'))return 'Explain the browser or component behavior first, then walk through your implementation, state/data flow, accessibility and performance considerations, and how you would test it.'+context;
  if(t.includes('time complexity')||t.includes('cycle')||t.includes('algorithm'))return 'State the approach first, walk through the key steps, then give time and space complexity and test an edge case. Mention why you chose this approach over alternatives.'+context;
  if(t.includes('project')||t.includes('tell me')||t.includes('why do you'))return 'Use STAR: Situation, Task, Action, Result. Keep the story specific, explain your individual contribution, and include measurable impact where possible.'+context;
  if(t.includes('design')||t.includes('system')||t.includes('scale'))return 'Clarify requirements, propose a simple architecture, explain data flow and trade-offs, then cover scale, reliability, security, observability, and failure cases.'+context;
  return 'Start with a concise definition or approach, give a concrete example from your work or study, explain your reasoning and trade-offs, and finish with how you would validate the result.'+context
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

function renderTopics(pack,jdKeywords){
  const topics=[...pack.topics];
  topics.unshift(jdKeywords.length?`JD focus: ${jdKeywords.map(x=>x.replace(/\b\w/g,c=>c.toUpperCase())).join(' · ')}`:'JD focus: add a job description for more targeted revision');
  renderList('topics',topics);
}

async function loadExperiences(r,c){
  const box=$('experienceList');
  if(!API){box.innerHTML='<div class="research-empty">Community reports require the live API.</div>';return}
  try{
    const res=await fetch(API+'/experiences/'+encodeURIComponent(r)+`?company=${encodeURIComponent(c)}`);
    if(!res.ok)throw new Error('experience request failed');
    const data=await res.json();
    const items=data.items||[];
    if(!items.length){box.innerHTML='<div class="research-empty">No candidate-reported experiences yet. Be the first to add context to a question.</div>';return}
    box.innerHTML=items.map((x,i)=>{
      const contexts=(x.contexts||[]).map(ctx=>`<span class="experience-chip">${escapeHtml(ctx.company||'Company not specified')} · ${escapeHtml(ctx.round)} · ${escapeHtml(ctx.difficulty)}</span>`).join('');
      return `<div class="experience-item"><div><strong>${String(i+1).padStart(2,'0')} · ${escapeHtml(x.question)}</strong><span class="report-count">${x.reports} report${x.reports===1?'':'s'}</span></div><div class="experience-context">${contexts}</div></div>`;
    }).join('');
  }catch(e){box.innerHTML='<div class="research-empty">Could not load community experiences right now.</div>'}
}

function openReport(item){
  reportQuestion=item;
  $('reportQuestion').textContent=item.q;
  $('reportCompany').value=company.value.trim();
  $('reportRound').value='Technical';
  $('reportDifficulty').value='Medium';
  $('reportStatus').textContent='';
  $('reportModal').classList.remove('hidden');
}
function closeReport(){reportQuestion=null;$('reportModal').classList.add('hidden')}

async function submitReport(){
  if(!reportQuestion||!API)return;
  const status=$('reportStatus');status.textContent='Saving…';
  try{
    const res=await fetch(API+'/experiences',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question_id:reportQuestion.id,role:currentRole,company:$('reportCompany').value.trim(),interview_round:$('reportRound').value,difficulty:$('reportDifficulty').value})});
    const data=await res.json();
    if(!res.ok)throw new Error(data.detail||'Could not save report');
    status.textContent=data.duplicate?'You already reported this question from this browser.':'Saved — thank you for improving the community signal.';
    if(!data.duplicate){
      const button=document.querySelector(`.report[data-id="${reportQuestion.id}"]`);if(button){button.classList.add('reported');button.textContent='✓ Experience added'}
      await loadExperiences(currentRole,company.value.trim());
    }
    setTimeout(closeReport,900);
  }catch(e){status.textContent=e.message||'Could not save report.'}
}

async function generate(){
  const r=(role.value||'Software Engineer').trim();
  const c=(company?.value||'').trim();
  const jdText=jd.value.trim();
  currentRole=r;
  $('resultTitle').textContent=r;
  $('resultSub').textContent=jdText?(c?`Customized from your job description, role patterns, and ${c} web research.`:'Customized from your job description + role patterns.'):(c?`Role-based preparation with ${c} web research.`:'Role-based preparation pack.');
  let data=null;
  if(API){try{const res=await fetch(API+'/prep',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({role:r,job_description:jdText})});if(res.ok)data=await res.json()}catch(e){console.warn('InterviewLens API unavailable; using local pack.')}}
  const p=choosePack(r+' '+jdText);
  const jdKeywords=data?.jd_keywords||[];
  currentQuestions=(data&&data.questions?.length)?data.questions.map(x=>({id:x.id,q:x.question,count:x.confirmations})):p.questions||[];
  renderQuestions(currentQuestions,jdKeywords);
  renderTopics(p,jdKeywords);renderList('behavioral',p.behavioral);renderList('checklist',p.checklist);
  results.classList.remove('hidden');renderResearch(null);
  loadExperiences(r,c);
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
        const countEl=button.parentElement.querySelector('small b');if(countEl)countEl.textContent=d.confirmations;
        button.classList.add('confirmed');button.textContent='✓ Asked in an interview';button.dataset.confirmed='1';
        localStorage.setItem('confirmed:'+id,'1');
        const item=items.find(x=>x.id===id);if(item)item.count=d.confirmations;
        updateSignal(items);return
      }
    }catch(e){console.warn('Community confirmation failed; using local fallback.')}}
  const k='asked:'+q.toLowerCase().replace(/\W+/g,'-');
  if(localStorage.getItem(k))return;
  localStorage.setItem(k,'1');button.classList.add('confirmed');button.textContent='✓ Asked in an interview';button.dataset.confirmed='1';
  const countEl=button.parentElement.querySelector('small b');if(countEl)countEl.textContent='1';updateSignal(items)
}

function renderQuestions(items,jdKeywords=[]){
  const displayItems=items.length?items:[];
  $('questions').innerHTML=displayItems.map((x,i)=>{
    const q=x.q||x,n=Number(x.count)||0,already=x.id&&localStorage.getItem('confirmed:'+x.id),reported=x.id&&localStorage.getItem('reported:'+x.id);
    return `<div class="q"><div class="q-head"><span class="q-num">${String(i+1).padStart(2,'0')}</span><p>${escapeHtml(q)}</p></div><small>${x.id?'Community reports':'Recommended for this role/JD'} · Confirmations: <b>${n}</b></small><details class="answer"><summary>How should I answer?</summary><p>${escapeHtml(answerGuide(q,jdKeywords))}</p></details><div class="q-actions"><button class="asked ${already?'confirmed':''}" data-id="${x.id||''}" data-confirmed="${already?'1':'0'}">${already?'✓ Asked in an interview':'I was asked this'}</button>${x.id?`<button class="report ${reported?'reported':''}" data-id="${x.id}">${reported?'✓ Experience added':'Add interview context'}</button>`:''}</div></div>`
  }).join('');
  const buttons=[...document.querySelectorAll('.asked')];
  buttons.forEach((b,i)=>{const item=displayItems[i],q=item.q||item;b.onclick=()=>confirm(item.id,q,b,displayItems)});
  document.querySelectorAll('.report').forEach((b,i)=>b.onclick=()=>openReport(displayItems.find(x=>String(x.id)===String(b.dataset.id))));
  updateSignal(displayItems)
}

function updateSignal(items=[]){
  const communityTotal=items.reduce((sum,item)=>sum+(Number(item.count)||0),0);
  const localTotal=new Set([...Object.keys(localStorage).filter(k=>k.startsWith('asked:')), ...Object.keys(localStorage).filter(k=>k.startsWith('confirmed:'))]).size;
  $('signalNumber').textContent=communityTotal;
  $('confidence').textContent=communityTotal?`${communityTotal} candidate confirmation${communityTotal===1?'':'s'} across these questions`:'Community confidence: building';
  const localLabel=$('confidence');if(localLabel&&localTotal&&communityTotal===0)localLabel.textContent='Your confirmation is recorded locally while this pack builds community evidence';
}

$('generate').onclick=generate;
$('reset').onclick=()=>{results.classList.add('hidden');role.focus();window.scrollTo({top:0,behavior:'smooth'})};
$('closeReport').onclick=closeReport;
$('cancelReport').onclick=closeReport;
$('submitReport').onclick=submitReport;
$('reportModal').addEventListener('click',e=>{if(e.target.id==='reportModal')closeReport()});
document.querySelectorAll('.examples button').forEach(b=>b.onclick=()=>{role.value=b.dataset.role;role.focus()});
updateSignal();
