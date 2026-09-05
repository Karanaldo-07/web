(() => {
  const STORAGE_KEY = 'interviewlens-theme';
  const root = document.documentElement;

  function readTheme() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === 'dark' || saved === 'light') return saved;
    } catch (_) {}
    return 'light';
  }

  function saveTheme(theme) {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (_) {}
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

  applyTheme(readTheme());

  document.addEventListener('DOMContentLoaded', () => {
    applyTheme(readTheme());

    const button = document.getElementById('themeToggle');
    if (!button) return;

    button.addEventListener('click', () => {
      const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
      saveTheme(next);
      applyTheme(next);
    });
  });
})();
