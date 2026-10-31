import { readFile, writeFile, readdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const folder = path.join(root, 'docs', 'apresentacao');
const excluded = new Set(['README.md', '04-modelo-de-dados.md', '06-conformidade-fase1.md']);
const files = (await readdir(folder)).filter(name => name.endsWith('.md') && !excluded.has(name));
files.sort((a, b) => a.localeCompare(b));
const chapters = await Promise.all(files.map(async file => ({
  file,
  markdown: await readFile(path.join(folder, file), 'utf8'),
})));
const template = await readFile(path.join(folder, 'template.html'), 'utf8');
const data = JSON.stringify(chapters).replaceAll('<', '\\u003c');
await writeFile(path.join(folder, 'index.html'), template.replace('/* WIKI_DATA */', data));
console.log(`Apresentação gerada: ${chapters.length} arquivos em docs/apresentacao/index.html`);
