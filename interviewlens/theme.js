(function(){
  const key='interviewlens-theme';
  const root=document.documentElement;
  function getTheme(){
    const saved=localStorage.getItem(key);
    if(saved==='dark'||saved==='light')return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
  }
  function apply(theme){
    root.dataset.theme=theme;
    const button=document.getElementById('themeToggle');
    if(button){
      const dark=theme==='dark';
      button.textContent=dark?'☀️':'🌙';
      button.setAttribute('aria-label',dark?'Switch to light mode':'Switch to dark mode');
      button.setAttribute('title',dark?'Switch to light mode':'Switch to dark mode');
    }
  }
  apply(getTheme());
  document.addEventListener('DOMContentLoaded',function(){
    apply(getTheme());
    const button=document.getElementById('themeToggle');
    if(!button)return;
    button.addEventListener('click',function(){
      const next=root.dataset.theme==='dark'?'light':'dark';
      localStorage.setItem(key,next);
      apply(next);
    });
    const media=window.matchMedia('(prefers-color-scheme: dark)');
    media.addEventListener?.('change',function(){
      if(!localStorage.getItem(key))apply(media.matches?'dark':'light');
    });
  });
})();
