(() => {
  const STORAGE_KEY = 'interviewlens-theme';
  const root = document.documentElement;
  const prefersDark = () => window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false;

  function readTheme() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === 'dark' || saved === 'light') return saved;
    } catch (_) {}
    return prefersDark() ? 'dark' : 'light';
  }

  function saveTheme(theme) {
    try { localStorage.setItem(STORAGE_KEY, theme); } catch (_) {}
  }

  function applyTheme(theme) {
    root.dataset.theme = theme;
    const button = document.getElementById('themeToggle');
    if (!button) return;
    const dark = theme === 'dark';
    button.textContent = dark ? '☀️' : '🌙';
    button.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
    button.setAttribute('title', dark ? 'Switch to light mode' : 'Switch to dark mode');
  }

  function polishUI() {
    const style = document.createElement('style');
    style.textContent = `
      .input-guidance{margin:9px auto 0;width:min(850px,100%);color:var(--text-soft);font-size:12px;line-height:1.45;text-align:center}
      .examples{align-items:center}
      .examples::before{content:'Try a role';color:var(--text-soft);font-size:11px;font-weight:650;margin-right:2px}
      .results-meta{display:flex;gap:7px;flex-wrap:wrap;margin-top:9px}
      .results-meta span{padding:4px 8px;border:1px solid var(--border);border-radius:999px;color:var(--text-soft);font-size:11px;background:var(--surface)}
      .card-title h3{font-weight:720}
      .experience-item,.lead-item,.source,.report-question,.modal-panel input,.modal-panel select,.asked,.report{border-color:var(--border)!important;background:var(--surface)!important;color:var(--text)}
      .experience-item strong,.lead-item p{color:var(--text)}
      .experience-chip{background:var(--surface-subtle)!important;border-color:var(--border)!important;color:var(--text-muted)!important}
      .report-count,.source a,.answer summary{color:var(--accent)!important}
      .modal{background:rgb(15 17 23 / 58%)}
      .modal-panel{background:var(--surface)!important;color:var(--text)}
      .primary-action{background:var(--text);color:var(--bg)}
      .section-note{color:var(--text-muted)}
      @media(max-width:760px){.input-guidance{text-align:left}.examples::before{width:100%;text-align:left;margin-bottom:1px}}
    `;
    document.head.appendChild(style);

    const hero = document.querySelector('.hero');
    const search = document.querySelector('.search');
    if (hero && search && !document.getElementById('inputGuidance')) {
      const hint = document.createElement('p');
      hint.id = 'inputGuidance';
      hint.className = 'input-guidance';
      hint.textContent = 'Start with a role. Add a company or job description for more targeted results.';
      search.insertAdjacentElement('afterend', hint);
    }

    const roleInput = document.getElementById('role');
    const companyInput = document.getElementById('company');
    const jdInput = document.getElementById('jd');
    if (roleInput) roleInput.placeholder = 'Job title — e.g. Software Engineer, Data Analyst';
    if (companyInput) companyInput.placeholder = 'Optional company — e.g. Microsoft, TCS, Infosys';
    if (jdInput) jdInput.placeholder = 'Optional: paste the job description for a more targeted prep pack…';

    const heroTitle = document.querySelector('.hero h1');
    if (heroTitle) heroTitle.innerHTML = 'Prepare for the questions<br><span>that matter most.</span>';
    const lead = document.querySelector('.hero .lead');
    if (lead) lead.textContent = 'Search by role, add a company or paste a job description. Get likely interview questions, what to revise, candidate-reported experiences, and targeted research.';

    const headings = document.querySelectorAll('#results .card-title h3, #results .card > h3');
    headings.forEach(h => {
      const replacements = {
        '🔥 Top interview questions':'Top interview questions',
        '🧑‍💼 Candidate interview experiences':'Candidate interview experiences',
        '🌐 Web research':'Web research',
        '🧠 Topics to revise':'Topics to revise',
        '💬 Behavioral questions':'Behavioral questions',
        '✅ Before the interview':'Before the interview',
        '⭐ Community signal':'Community signal'
      };
      if (replacements[h.textContent]) h.textContent = replacements[h.textContent];
    });

    const resultHead = document.querySelector('.result-head');
    if (resultHead && !document.getElementById('resultsMeta')) {
      const meta = document.createElement('div');
      meta.id = 'resultsMeta';
      meta.className = 'results-meta';
      ['Questions','Community reports','Web research'].forEach(text => {
        const item = document.createElement('span');
        item.textContent = text;
        meta.appendChild(item);
      });
      const resultSub = document.getElementById('resultSub');
      if (resultSub) resultSub.insertAdjacentElement('afterend', meta);
    }
  }

  applyTheme(readTheme());

  document.addEventListener('DOMContentLoaded', () => {
    applyTheme(readTheme());
    polishUI();
    const button = document.getElementById('themeToggle');
    if (!button) return;
    button.addEventListener('click', () => {
      const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
      saveTheme(next);
      applyTheme(next);
    });
    const media = window.matchMedia?.('(prefers-color-scheme: dark)');
    media?.addEventListener?.('change', event => {
      try {
        if (!localStorage.getItem(STORAGE_KEY)) applyTheme(event.matches ? 'dark' : 'light');
      } catch (_) { applyTheme(event.matches ? 'dark' : 'light'); }
    });
  });
})();
