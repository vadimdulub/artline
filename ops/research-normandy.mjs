// Bounded official collection-page evidence capture. No DB or image requests.
import { parse } from '../apps/web/node_modules/parse5/dist/index.js';
import { createHash } from 'node:crypto';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as pause } from 'node:timers/promises';

const root = resolve(fileURLToPath(new URL('..', import.meta.url)));
const out = join(root, 'content/imports/normandy-primary-20260910');
const sha = b => createHash('sha256').update(b).digest('hex');
const clean = s => s.replace(/\s+/g, ' ').trim();
const attr = (n, key) => n.attrs?.find(a => a.name === key)?.value || '';
const hasClass = (n, c) => attr(n, 'class').split(/\s+/).includes(c);
function nodes(n, predicate) {
  return [...(predicate(n) ? [n] : []), ...(n.childNodes || []).flatMap(c => nodes(c, predicate))];
}
function text(n) {
  if (n.nodeName === '#text') return n.value;
  if (n.tagName === 'br') return '\n';
  if (['script', 'style'].includes(n.tagName)) return '';
  return (n.childNodes || []).map(text).join('');
}
const first = (n, fn) => nodes(n, fn)[0];
const content = (n, c) => first(n, a => hasClass(a, c));
function links(doc, base, prefix) {
  return [...new Set(nodes(doc, n => n.tagName === 'a').map(n => {
    try { return new URL(attr(n, 'href'), base); } catch { return null; }
  }).filter(u => u && u.origin === new URL(base).origin && u.pathname.startsWith(prefix) && !u.search && !u.hash)
    .map(u => u.href))].sort();
}
export function extract(html, url, source) {
  const doc = parse(html);
  const title = clean(text(first(doc, n => attr(n, 'id') === 'page-title') || {}));
  if (source === 'muma') {
    const legends = nodes(doc, n => hasClass(n, 'legend_visuel'));
    // A group/gallery page must not become a single physical artwork.
    if (legends.length !== 1 || !content(doc, 'visuel_oeuvre_unique')) return { url, title, state: 'group_or_layout_review' };
    const lines = text(legends[0]).split('\n').map(clean).filter(Boolean);
    return { url, title, source, lines, state: 'extracted',
      canonical: attr(first(doc, n => n.tagName === 'link' && attr(n, 'rel') === 'canonical') || {}, 'href') };
  }
  const article = first(doc, n => n.tagName === 'article' && hasClass(n, 'node-oeuvre'));
  if (!article) return { url, title, state: 'layout_review' };
  const artist = content(article, 'artiste');
  return { url, title, source, state: 'extracted',
    artist: clean(text(first(artist || {}, n => n.tagName === 'h2') || {})),
    artist_details: clean(text(first(artist || {}, n => n.tagName === 'p') || {})),
    details: clean(text(content(article, 'details') || {})),
    canonical: attr(first(doc, n => n.tagName === 'link' && attr(n, 'rel') === 'canonical') || {}, 'href'),
    shortlink: attr(first(doc, n => n.tagName === 'link' && attr(n, 'rel') === 'shortlink') || {}, 'href') };
}
async function save(path, data) {
  const bytes = typeof data === 'string' || Buffer.isBuffer(data) ? data : JSON.stringify(data, null, 2) + '\n';
  try { await writeFile(path, bytes, { flag: 'wx', mode: 0o600 }); }
  catch (e) { if (e.code !== 'EEXIST' || !Buffer.from(await readFile(path)).equals(Buffer.from(bytes))) throw e; }
}
const lastRequest = new Map();
async function capture(url) {
  const u = new URL(url);
  if (!['www.muma-lehavre.fr', 'mbarouen.fr'].includes(u.host) || u.protocol !== 'https:' || u.search || u.hash || u.username ||
      !(/^\/fr\/(collections(?:\/|$)|oeuvres\/|mentions-legales$)/.test(u.pathname) || u.pathname === '/robots.txt')) throw Error('URL outside approved source scope');
  const file = sha(url) + '.html';
  try {
    const receipt = JSON.parse(await readFile(join(out, file + '.snapshot.json'), 'utf8'));
    const b = await readFile(join(out, file));
    if (receipt.url !== url || receipt.sha256 !== sha(b) || receipt.bytes !== b.length) throw Error('Changed capture');
    return { html: b.toString('utf8'), file, receipt };
  } catch (e) { if (e.code !== 'ENOENT') throw e; }
  await pause(Math.max(0, 10500 - (Date.now() - (lastRequest.get(u.host) || 0))));
  lastRequest.set(u.host, Date.now());
  const r = await fetch(url, { redirect: 'manual', signal: AbortSignal.timeout(35000), headers: {
    'User-Agent': 'ArtlineMuseumResearch/1.0 (selected factual catalogue metadata; no images)', 'Accept': 'text/html,text/plain' } });
  if (r.status !== 200) throw Error(`${r.status} ${url}: stopped, no automatic retry`);
  let length = 0; const chunks = [];
  for await (const chunk of r.body) { length += chunk.length; if (length > 2 * 1024 * 1024) throw Error('Page exceeds 2 MiB'); chunks.push(chunk); }
  const b = Buffer.concat(chunks);
  const receipt = { url, sha256: sha(b), bytes: b.length, retrieved_at: new Date().toISOString() };
  await save(join(out, file), b); await save(join(out, file + '.snapshot.json'), receipt);
  console.log(`${u.host} ${u.pathname} ${b.length} bytes`);
  return { html: b.toString('utf8'), file, receipt };
}
async function run(source) {
  const base = source === 'muma' ? 'https://www.muma-lehavre.fr' : 'https://mbarouen.fr';
  await capture(base + '/robots.txt');
  await capture(base + '/fr/mentions-legales');
  const paths = source === 'muma' ? ['/fr/collections/oeuvres-commentees/incontournable'] : [
    '/fr/collections/l-impressionnisme', '/fr/collections/la-renaissance',
    '/fr/collections/l-europe-baroque', '/fr/collections/le-grand-siecle-francais',
    '/fr/collections/le-romantisme', '/fr/collections/le-paysage'];
  const prefix = source === 'muma' ? '/fr/collections/oeuvres-commentees/' : '/fr/oeuvres/';
  const candidates = new Set(); const indexes = [];
  for (const path of paths) {
    const page = await capture(base + path); indexes.push(page.receipt);
    for (const url of links(parse(page.html), base, prefix)) {
      if (source !== 'muma' || new URL(url).pathname.slice(prefix.length).includes('/')) candidates.add(url);
    }
  }
  if (candidates.size > 120 || candidates.size < 1) throw Error(`${source}: candidate cap/layout review (${candidates.size})`);
  const works = [];
  for (const url of [...candidates].sort()) {
    const p = await capture(url);
    works.push({ ...extract(p.html, url, source), snapshot: p.receipt, snapshot_file: p.file });
  }
  await save(join(out, source + '-facts.json'), { source, indexes, works, complete_for_selected_pages: true });
  console.log(`${source}: completed ${works.length} selected pages (not full collection)`);
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  await mkdir(out, { recursive: true, mode: 0o700 });
  const results = await Promise.allSettled(['muma', 'rouen'].map(run));
  for (let i = 0; i < results.length; i++) if (results[i].status === 'rejected') console.error(['muma','rouen'][i], results[i].reason);
  if (results.some(r => r.status === 'rejected')) process.exitCode = 1;
}
