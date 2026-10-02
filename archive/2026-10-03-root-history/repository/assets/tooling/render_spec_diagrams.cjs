#!/usr/bin/env node
// Render the diagrams embedded in the single implementation specification.
// Usage: node render_spec_diagrams.cjs SPEC OUTPUT_DIR MERMAID_RUNTIME_DIR PLAYWRIGHT_MODULE [CHROMIUM_EXECUTABLE]
// MERMAID_RUNTIME_DIR must contain node_modules/mermaid (tested: mermaid 11.12.0).
const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');

async function main() {
  const [specArg, outputArg, runtimeArg, playwrightArg, chromiumArg] = process.argv.slice(2);
  if (!specArg || !outputArg || !runtimeArg || !playwrightArg) {
    throw new Error('Expected SPEC OUTPUT_DIR MERMAID_RUNTIME_DIR PLAYWRIGHT_MODULE');
  }
  const spec = path.resolve(specArg);
  const output = path.resolve(outputArg);
  const runtime = path.resolve(runtimeArg);
  const { chromium } = require(path.resolve(playwrightArg));
  const markdown = await fs.readFile(spec, 'utf8');
  const blocks = [...markdown.matchAll(/```mermaid\n([\s\S]*?)\n```/g)];
  if (!blocks.length) throw new Error('No Mermaid diagrams in specification');
  await fs.mkdir(output, { recursive: true });
  const html = `<!doctype html><meta charset="utf-8"><style>
    html,body { margin:0; background:#fff; }
    #diagram { padding:24px; display:inline-block; }
    #diagram svg { max-width:none !important; }
    </style><div id="diagram"></div><script type="module">
    import mermaid from '/node_modules/mermaid/dist/mermaid.esm.min.mjs';
    mermaid.initialize({startOnLoad:false,securityLevel:'strict',theme:'base',
      fontFamily:'Arial, Apple SD Gothic Neo, sans-serif',
      themeVariables:{primaryColor:'#eef2ff',primaryTextColor:'#172554',
        primaryBorderColor:'#64748b',lineColor:'#475569',fontSize:'16px',
        actorBkg:'#f1f5f9',actorBorder:'#64748b',actorTextColor:'#0f172a',
        noteBkgColor:'#fefce8',noteBorderColor:'#eab308',noteTextColor:'#422006'},
      flowchart:{useMaxWidth:false,htmlLabels:true,nodeSpacing:35,rankSpacing:50},
      sequence:{useMaxWidth:false,diagramMarginX:25,diagramMarginY:25,
        actorMargin:40,messageMargin:32,noteMargin:15,wrap:true,width:170}});
    window.draw=async function(id,source) {
      await mermaid.parse(source);
      const rendered=await mermaid.render(id,source);
      document.querySelector('#diagram').innerHTML=rendered.svg;
      await document.fonts.ready;
      return rendered.svg;
    };
    </script>`;
  const server = http.createServer(async (request, response) => {
    try {
      const url = new URL(request.url, 'http://localhost');
      if (url.pathname === '/') {
        response.setHeader('Content-Type', 'text/html; charset=utf-8');
        response.end(html);
        return;
      }
      const requested = path.resolve(runtime, '.' + decodeURIComponent(url.pathname));
      if (!requested.startsWith(runtime + path.sep)) throw new Error('Invalid asset path');
      const bytes = await fs.readFile(requested);
      response.setHeader('Content-Type', requested.endsWith('.css') ? 'text/css' : 'text/javascript');
      response.end(bytes);
    } catch (_) {
      response.writeHead(404);
      response.end();
    }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  const manifest = { specification: path.basename(spec), specification_sha256:
    crypto.createHash('sha256').update(markdown).digest('hex'), renderer:'mermaid 11.12.0', diagrams:[] };
  try {
    browser = await chromium.launch({ headless:true, executablePath:chromiumArg || chromium.executablePath() });
    const page = await browser.newPage({ viewport:{width:1900,height:1200}, deviceScaleFactor:1 });
    await page.goto(`http://127.0.0.1:${server.address().port}/`);
    await page.waitForFunction(() => typeof window.draw === 'function');
    for (const [index, block] of blocks.entries()) {
      const name = `diagram-${String(index + 1).padStart(2,'0')}`;
      const headings = markdown.slice(0, block.index).match(/^#{1,4} .+$/gm);
      const title = headings?.at(-1)?.replace(/^#+ /,'') || name;
      const svg = await page.evaluate(async ({name,source}) => window.draw(name,source),
        {name,source:block[1]});
      await fs.writeFile(path.join(output,name+'.svg'), svg);
      await fs.writeFile(path.join(output,name+'.mmd'), block[1]+'\n');
      await page.locator('#diagram').screenshot({path:path.join(output,name+'.png')});
      const box = await page.locator('#diagram').boundingBox();
      const item={name,title,width:Math.ceil(box.width),height:Math.ceil(box.height),
        source_sha256:crypto.createHash('sha256').update(block[1]).digest('hex')};
      manifest.diagrams.push(item);
      process.stdout.write(JSON.stringify(item)+'\n');
    }
    await fs.writeFile(path.join(output,'render-manifest.json'), JSON.stringify(manifest,null,2)+'\n');
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}
main().catch(error => { process.stderr.write(error.stack+'\n'); process.exitCode=1; });
