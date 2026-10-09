import { readFile, writeFile, mkdir, cp, rm, realpath, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const source = path.join(repo, 'docs');
const output = path.join(repo, 'site');
const markedModule = process.env.DOCS_MARKED_MODULE;
const { marked } = await import(markedModule ? pathToFileURL(markedModule).href : 'marked');
const sha = text => createHash('sha256').update(text).digest('hex');
const escape = text => text.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const slug = text => text.toLowerCase().replace(/[`*]/g, '').replace(/[^\p{L}\p{N}_\- ]/gu, '').replace(/ /g, '-');
const htmlPath = file => file === 'README.md' ? 'index.html' : file.replace(/\.md$/, '.html');
const summary = await readFile(path.join(source, 'SUMMARY.md'), 'utf8');
const pages = [];
let group = 'Start here';
for (const line of summary.split('\n')) {
  if (line.startsWith('## ')) group = line.slice(3);
  const link = line.match(/^\* \[(.+)\]\((.+\.md)\)$/);
  if (link) pages.push({ title: link[1], file: link[2], group });
}
const manifest = JSON.parse(await readFile(path.join(source, 'assets/diagrams/render-manifest.json'), 'utf8'));
const diagrams = new Map(manifest.diagrams.map(d => [d.source_sha256, d]));
await rm(output, { recursive: true, force: true });
await mkdir(output, { recursive: true });
await cp(path.join(source, 'assets'), path.join(output, 'assets'), { recursive: true });
const relative = (from, to) => path.posix.relative(path.posix.dirname(from), to) || path.posix.basename(to);
const attachments = new Map();
const search = [];
for (let i = 0; i < pages.length; i++) {
  const page = pages[i];
  const destination = htmlPath(page.file);
  const markdown = await readFile(path.join(source, page.file), 'utf8');
  const headings = [], used = new Map();
  const renderer = new marked.Renderer();
  renderer.heading = token => {
    const base = slug(token.text);
    const count = used.get(base) || 0;
    used.set(base, count + 1);
    const id = base + (count ? `-${count}` : '');
    if (token.depth > 1 && token.depth < 4) headings.push({ text: token.text.replace(/[`*]/g, ''), id, depth: token.depth });
    return `<h${token.depth} id="${escape(id)}">${renderer.parser.parseInline(token.tokens)}</h${token.depth}>\n`;
  };
  renderer.code = token => {
    if (token.lang === 'mermaid') {
      const diagram = diagrams.get(sha(token.text));
      if (!diagram) throw new Error(`Unrendered diagram in ${page.file}`);
      const href = relative(destination, `assets/diagrams/${diagram.name}.svg`);
      return `<figure><a href="${href}" target="_blank" rel="noopener"><img src="${href}" alt="${escape(diagram.title)}" loading="lazy"></a><figcaption>Click the diagram to open it full size.</figcaption></figure>`;
    }
    return `<pre><code class="language-${escape(token.lang || 'text')}">${escape(token.text)}</code></pre>\n`;
  };
  let content = marked.parse(markdown, { renderer, gfm: true });
  content = content.replace(/href="([^"#][^"]*\.md)(#[^"]*)?"/g, (all, file, anchor = '') => {
    if (/^(?:[a-z]+:|\/)/i.test(file)) return all;
    const target = path.posix.normalize(path.posix.join(path.posix.dirname(page.file), file));
    if (target === 'SUMMARY.md') return `href="${relative(destination, 'index.html')}${anchor}"`;
    if (pages.some(p => p.file === target)) return `href="${relative(destination, htmlPath(target))}${anchor}"`;
    // Preserve directly linked source documents without publishing the whole repository.
    const attachment = path.resolve(source, target);
    if (!attachment.startsWith(repo + path.sep)) throw new Error(`Link outside repository in ${page.file}: ${file}`);
    const attachmentPath = `repository/${path.relative(repo, attachment).split(path.sep).join('/')}`;
    attachments.set(attachmentPath, attachment);
    return `href="${relative(destination, attachmentPath)}${anchor}" download title="Download source Markdown"`;
  });
  const linkTo = p => relative(destination, htmlPath(p.file));
  let lastGroup = '';
  const navigation = pages.map(p => {
    const heading = lastGroup !== p.group ? `<div class="nav-group">${escape(p.group)}</div>` : '';
    lastGroup = p.group;
    return `${heading}<a ${p.file === page.file ? 'aria-current="page"' : ''} href="${linkTo(p)}">${escape(p.title)}</a>`;
  }).join('\n');
  const toc = headings.map(h => `<a class="depth-${h.depth}" href="#${escape(h.id)}">${escape(h.text)}</a>`).join('');
  const adjacent = (p, label) => p ? `<a href="${linkTo(p)}"><small>${label}</small>${escape(p.title)}</a>` : '<span></span>';
  const base = relative(destination, 'index.html').replace(/index\.html$/, '');
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(page.title)} · Baton</title><link rel="stylesheet" href="${base}style.css"></head><body>
<header><button id="menu" aria-label="Open table of contents" aria-expanded="false">☰</button><a class="brand" href="${base}index.html">Baton <span>Implementation docs</span></a><a href="https://github.com/djm07073/baton-research/tree/main/docs" class="github">GitHub</a></header>
<aside id="sidebar"><label for="search">Search docs</label><input id="search" type="search" placeholder="Search terms" autocomplete="off"><div id="results" aria-live="polite"></div><nav id="navigation" aria-label="Documentation navigation">${navigation}</nav></aside>
<main><div class="breadcrumb">${escape(page.group)}</div><article>${content}</article><div class="page-nav">${adjacent(pages[i - 1], 'Previous')}${adjacent(pages[i + 1], 'Next')}</div></main><aside class="toc"><div>On this page</div>${toc}</aside>
<script>window.DOCS_BASE=${JSON.stringify(base)};</script><script src="${base}app.js" defer></script></body></html>`;
  await mkdir(path.dirname(path.join(output, destination)), { recursive: true });
  await writeFile(path.join(output, destination), html);
  search.push({ title: page.title, group: page.group, url: destination, text: markdown.replace(/```[\s\S]*?```/g, '').replace(/<[^>]+>/g, '').replace(/[#*`|]/g, '') });
}
for (const [destination, attachment] of attachments) {
  const resolved = await realpath(attachment);
  if (!resolved.startsWith(repo + path.sep) || !(await stat(resolved)).isFile()) {
    throw new Error(`Source attachment is not a repository file: ${attachment}`);
  }
  await mkdir(path.dirname(path.join(output, destination)), { recursive: true });
  await cp(resolved, path.join(output, destination));
}
await writeFile(path.join(output, 'search.json'), JSON.stringify(search));
await cp(path.join(repo, 'assets/tooling/docs-style.css'), path.join(output, 'style.css'));
await cp(path.join(repo, 'assets/tooling/docs-app.js'), path.join(output, 'app.js'));
console.log(`Built ${pages.length} pages, ${diagrams.size} diagrams and ${attachments.size} source attachments in ${output}`);
