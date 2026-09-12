// Selected factual research only. No images, site crawl, database writes or retries.
import {parse} from '../apps/web/node_modules/parse5/dist/index.js';
import {nodes, text, attr, clean} from './research-icons.mjs';
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {setTimeout as pause} from 'node:timers/promises';
const args = process.argv.slice(2);
const captureDate = args[0] === '--date' ? args.splice(0, 2)[1] : '20260910';
if (!['20260910', '20260911'].includes(captureDate)) throw Error('Unreviewed capture directory');
const dir = `content/imports/greek-painter-review-${captureDate}`;
const hash = b => createHash('sha256').update(b).digest('hex');
const urls = args;
if (!urls.length || urls.length > 30) throw Error('Supply 1–30 selected museum HTML URLs');
await mkdir(dir, {recursive: true, mode: 0o700});
for (const url of urls) {
  const u = new URL(url);
  if (u.origin !== 'https://www.nationalgallery.gr' || u.search || u.hash || !/^\/(robots\.txt|oroi-chrisis\/|en\/(artist|artwork)\/[a-z0-9-]+\/)$/.test(u.pathname)) throw Error('Unreviewed route');
  const path = dir + '/' + hash(url) + '.html';
  let raw, snapshot;
  try {
    raw = await readFile(path); snapshot = JSON.parse(await readFile(path + '.snapshot.json'));
    if (snapshot.url !== url || snapshot.sha256 !== hash(raw)) throw Error('Changed source capture');
  } catch (e) {
    if (e.code !== 'ENOENT') throw e;
    await pause(2000);
    const response = await fetch(url, {redirect: 'manual', signal: AbortSignal.timeout(35000), headers: {'User-Agent': 'ArtlineMuseumResearch/1.0 (selected factual metadata for personal study; no images)', Accept: 'text/html,text/plain'}});
    if (response.status !== 200) throw Error(`${response.status}: stopped source without retry: ${url}`);
    const chunks = []; let bytes = 0;
    for await (const chunk of response.body) { bytes += chunk.length; if (bytes > 2 * 1024 * 1024) throw Error('Page budget exceeded'); chunks.push(chunk); }
    raw = Buffer.concat(chunks); snapshot = {url, retrieved_at: new Date().toISOString(), sha256: hash(raw), bytes: raw.length};
    await writeFile(path, raw, {flag: 'wx', mode: 0o600});
    await writeFile(path + '.snapshot.json', JSON.stringify(snapshot, null, 2) + '\n', {flag: 'wx', mode: 0o600});
  }
  const doc = parse(raw.toString());
  const main = nodes(doc, n => n.tagName === 'main')[0] || doc;
  const facts = nodes(main, n => ['h1','h2','h3','p'].includes(n.tagName)).map(n => clean(text(n))).filter(Boolean);
  const links = [...new Set(nodes(main, n => n.tagName === 'a').map(n => attr(n, 'href')).filter(h => /^https:\/\/www\.nationalgallery\.gr\/en\/artwork\/[a-z0-9-]+\/$/.test(h)))];
  console.log(JSON.stringify({url, snapshot, facts: facts.filter(s=>s.length<400).slice(0, 12), artworks: links}));
}
