const menu = document.getElementById('menu');
menu.addEventListener('click', () => {
  const expanded = document.body.classList.toggle('menu-open');
  menu.setAttribute('aria-expanded', String(expanded));
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') {
    document.body.classList.remove('menu-open');
    menu.setAttribute('aria-expanded', 'false');
  }
});
const input = document.getElementById('search');
const results = document.getElementById('results');
const navigation = document.getElementById('navigation');
let indexPromise;
let revision = 0;
input.addEventListener('input', async () => {
  const current = ++revision;
  const query = input.value.trim().toLocaleLowerCase();
  results.replaceChildren();
  navigation.hidden = !!query;
  if (!query) return;
  try {
    indexPromise ||= fetch(`${window.DOCS_BASE}search.json`).then(response => {
      if (!response.ok) throw new Error('search unavailable');
      return response.json();
    });
    const entries = await indexPromise;
    if (revision !== current) return;
    const words = query.split(/\s+/);
    const matches = entries.filter(entry => words.every(word => `${entry.title} ${entry.text}`.toLocaleLowerCase().includes(word)))
      .sort((a, b) => Number(b.title.toLocaleLowerCase().includes(query)) - Number(a.title.toLocaleLowerCase().includes(query)));
    for (const entry of matches) {
      const link = document.createElement('a');
      link.href = `${window.DOCS_BASE}${entry.url}`;
      link.textContent = entry.title;
      const group = document.createElement('small');
      group.textContent = entry.group;
      link.append(group);
      results.append(link);
    }
    if (!matches.length) results.textContent = 'No results found.';
  } catch {
    if (revision === current) results.textContent = 'Search is unavailable. Use the table of contents.';
  }
});
