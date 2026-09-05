(() => {
  const API = window.INTERVIEWLENS_API || 'https://interviewlens-api.vercel.app';
  let transcript = [];
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const originalFetch = window.fetch.bind(window);
  window.fetch = async (...args) => {
    const response = await originalFetch(...args);
    try {
      const url = typeof args[0] === 'string' ? args[0] : args[0]?.url || '';
      if (url.includes('/mock/evaluate')) {
        const copy = response.clone(); const evaluation = await copy.json();
        const body = args[1]?.body ? JSON.parse(args[1].body) : null;
        if (body) transcript.push({question: body.question, answer: body.answer, evaluation});
      }
    } catch (_) {}
    return response;
  };
  function install() {
    if (document.getElementById('aiReportButton') || !document.getElementById('mockDone')) return;
    const done = document.getElementById('mockDone');
    const observer = new MutationObserver(async () => {
      if (done.classList.contains('hidden') || !transcript.length || document.getElementById('aiReportButton')) return;
      const wrap = document.createElement('div'); wrap.className = 'mock-report-loader';
      wrap.innerHTML = '<button id="aiReportButton" class="primary-action">Generate AI interview report →</button><div id="aiReportArea"></div>';
      done.appendChild(wrap);
      document.getElementById('aiReportButton').addEventListener('click', generate);
    });
    observer.observe(done, {attributes:true, childList:true, subtree:true});
  }
  async function generate() {
    const btn = document.getElementById('aiReportButton'), area = document.getElementById('aiReportArea');
    btn.disabled = true; btn.textContent = 'Generating AI report…'; area.innerHTML = '<div class="mock-loading">Analyzing your interview performance…</div>';
    const role = (document.getElementById('role')?.value || 'Software Engineer').trim();
    const jd = (document.getElementById('jd')?.value || '').trim();
    try {
      const r = await originalFetch(API + '/mock/report', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({role, job_description:jd, questions:transcript.map(x=>x.question), results:transcript.map(x=>({question:x.question, answer:x.answer, evaluation:x.evaluation}))})});
      if (!r.ok) throw new Error('Report request failed');
      const x = await r.json(); area.innerHTML = markup(x); btn.remove();
    } catch (_) { area.innerHTML = '<div class="mock-error">AI report could not be generated right now. Your interview scores are still available above.</div>'; btn.disabled=false; btn.textContent='Try AI report again →'; }
  }
  function list(a){return (Array.isArray(a)?a:[]).map(x=>`<li>${esc(x)}</li>`).join('')}
  function markup(x){return `<div class="mock-report"><div class="report-headline">${esc(x.readiness||'Interview report')}</div><h3>${esc(x.headline||'Your interview performance')}</h3><p class="report-summary">${esc(x.summary||'')}</p><div class="mock-report-grid"><div class="mock-report-section"><h4>💪 Strengths</h4><ul>${list(x.strengths)}</ul></div><div class="mock-report-section"><h4>🎯 Weak areas</h4><ul>${list(x.weak_areas)}</ul></div><div class="mock-report-section"><h4>📚 Priority topics</h4><ul>${list(x.priority_topics)}</ul></div><div class="mock-report-section"><h4>🚀 Action plan</h4><ul>${list(x.action_plan)}</ul></div></div><div class="mock-report-section" style="margin-top:14px"><h4>❓ Recommended next questions</h4><ul>${list(x.next_questions)}</ul></div></div>`}
  install(); new MutationObserver(install).observe(document.documentElement,{childList:true,subtree:true});
})();
