export function initThemeSystem() {
  if (localStorage.getItem('siteTheme') === 'dark') {
    document.body.classList.add('dark-mode')
  }
}
