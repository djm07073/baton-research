const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const { chromium } = require('/Users/suhajin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const repo = '/Users/suhajin/dev/baton/monorepo/baton-research';
const root = path.join(repo, 'site');
const evidence = path.join(repo, 'assets/review/app-scheduler-20261009/browser');
(async () => {
  await fs.mkdir(evidence, { recursive: true });
  const summary = await fs.readFile(path.join(repo, 'docs/SUMMARY.md'), 'utf8');
  const pages = [...summary.matchAll(/^\* \[[^\]]+\]\(([^)]+)\)/gm)].map(m => m[1] === 'README.md' ? 'index.html' : m[1].replace(/\.md$/, '.html'));
  const server = http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url, 'http://127.0.0.1');
      const file = path.resolve(root, '.' + decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname));
      if (!file.startsWith(root + path.sep)) throw new Error('outside root');
      const type = {'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json','.svg':'image/svg+xml','.png':'image/png'}[path.extname(file)] || 'application/octet-stream';
      res.setHeader('Content-Type', type);res.end(await fs.readFile(file));
    } catch (_) { res.writeHead(404);res.end(); }
  });
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  const base = `http://127.0.0.1:${server.address().port}/`;
  let browser;
  const report = {checked_at:new Date().toISOString(),pages:[],screenshots:[],failures:[]};
  try {
    browser = await chromium.launch({headless:true,executablePath:'/Users/suhajin/Library/Caches/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-mac-arm64/chrome-headless-shell'});
    const page = await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
    page.on('pageerror',error => report.failures.push(String(error)));
    for (const file of pages) {
      const response = await page.goto(base + file);
      await page.locator('article h1').waitFor();
      for (const img of await page.locator('article img').all()) {
        await img.scrollIntoViewIfNeeded();
        await img.evaluate(node => node.decode());
      }
      const result = await page.evaluate(() => ({title:document.title,h1:document.querySelector('article h1').textContent,images:[...document.querySelectorAll('article img')].map(i=>({loaded:i.complete && i.naturalWidth>0,src:i.getAttribute('src')})),nav:document.querySelectorAll('#navigation a').length}));
      report.pages.push({file,status:response.status(),...result});
      if(response.status()!==200 || result.nav!==pages.length || result.images.some(i=>!i.loaded)) report.failures.push(file);
    }
    for(const file of ['overview/architecture.html','baton/README.html','baton/interfaces.html','overview/rust-interfaces.html']) {
      await page.goto(base+file);await page.locator('article h1').waitFor();
      const output=file.replaceAll('/','-')+'.png';
      await page.screenshot({path:path.join(evidence,output),fullPage:false});report.screenshots.push(output);
    }
    await page.goto(base+'baton/interfaces.html');
    await page.locator('#search').fill('durable custody');
    await page.waitForFunction(()=>document.querySelector('#results').textContent.length>0);
    report.search_results=await page.locator('#results').innerText();
    if(!report.search_results.trim())report.failures.push('empty search');
    await page.setViewportSize({width:390,height:844});
    await page.goto(base+'baton/interfaces.html');
    await page.locator('#menu').click();
    report.mobile_menu=await page.locator('#menu').getAttribute('aria-expanded');
    if(report.mobile_menu!=='true')report.failures.push('mobile menu');
    await page.locator('#menu').click();
    await page.screenshot({path:path.join(evidence,'baton-interfaces-mobile.png'),fullPage:false});
    report.screenshots.push('baton-interfaces-mobile.png');
    for (const width of [390, 1440]) {
      await page.setViewportSize({width, height:width===390?844:1000});
      await page.goto(base+'baton/README.html');
      await page.locator('#when-speculative-execution-begins').scrollIntoViewIfNeeded();
      const output = `baton-roles-${width}.png`;
      await page.screenshot({path:path.join(evidence,output),fullPage:false});
      report.screenshots.push(output);
    }
    await fs.writeFile(path.join(evidence,'verification.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify({pages:report.pages.length,images:report.pages.reduce((n,p)=>n+p.images.length,0),screenshots:report.screenshots,failures:report.failures}));
    process.exitCode=report.failures.length?1:0;
  } finally {if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(error=>{console.error(error);process.exitCode=1;});
