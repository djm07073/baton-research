import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const page = await readFile(path.join(repo, 'docs/overview/rust-interfaces.md'), 'utf8');
const blocks = [...page.matchAll(/```rust,ignore\n([\s\S]*?)\n```/g)].map(match => match[1]);
if (!blocks.length) throw new Error('No Rust API excerpts found');
const body = blocks.join('\n\n');
const contents = '// @generated from docs/overview/rust-interfaces.md; edit that Markdown source.\n'
  + '// Existing Commonware API excerpts; not standalone declarations or protocol implementation.\n\n'
  + body + '\n';
const directory = path.join(repo, 'docs/assets/interfaces');
await mkdir(directory, { recursive: true });
await writeFile(path.join(directory, 'baton.rs'), contents);
console.log(`Exported ${blocks.length} Rust API excerpts to docs/assets/interfaces/baton.rs`);
