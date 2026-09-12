// Bounded, resumable primary-source capture; no DB writes or image downloads.
import { parse } from '../apps/web/node_modules/parse5/dist/index.js';
import { createHash } from 'node:crypto';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';
import { setTimeout as pause } from 'node:timers/promises';
const out = fileURLToPath(new URL('../content/imports/icons-primary-20260910/', import.meta.url));
const sha = b => createHash('sha256').update(b).digest('hex');
const hosts = new Set(['www.ebyzantinemuseum.gr', 'ikonen-museum.com', 'kreml.ru', 'collectiononline.kreml.ru']);
export const text = n => n.nodeName === '#text' ? n.value : ['script','style'].includes(n.tagName) ? '' : (n.childNodes || []).map(text).join(n.tagName === 'li' || n.tagName === 'p' ? ' ' : '');
export const nodes = (n, f) => [...(f(n) ? [n] : []), ...(n.childNodes || []).flatMap(c => nodes(c, f))];
export const attr = (n, key) => n.attrs?.find(a => a.name === key)?.value || '';
export const clean = s => s.replace(/\s+/g, ' ').trim();
export function extract(html, url) {
  const doc = parse(html);
  return {url, headings: nodes(doc,n => ['h1','h2'].includes(n.tagName)).map(n => clean(text(n))),
    description: nodes(doc,n=>attr(n,'class').split(/\s+/).includes('description')).map(n=>clean(text(n))),
    facts: nodes(doc,n => ['p','li'].includes(n.tagName) && !(n.childNodes || []).some(c => ['li','ul','ol','p'].includes(c.tagName))).map(n => clean(text(n))).filter(Boolean),
    links: [...new Set(nodes(doc,n => n.tagName === 'a').map(n => {try {return new URL(attr(n,'href'),url).href;} catch {return '';}}))].filter(Boolean)};
}
export async function capture(url) {
  const u = new URL(url);
  if (!hosts.has(u.host) || u.protocol !== 'https:' || u.username || u.password || u.hash) throw Error('Unapproved URL');
  // Only reviewed catalogue HTML/robots routes. In particular KAMIS /api/
  // (including its image route) is disallowed by robots and never requested.
  const permitted = u.pathname === '/robots.txt' && !u.search ||
    u.host === 'www.ebyzantinemuseum.gr' && u.pathname === '/' &&
      ['bxm.en.terms','bxm.en.collections','bxm.en.exhibit'].includes(u.searchParams.get('i')) &&
      [...u.searchParams.keys()].every(k=>['i','id','c','page'].includes(k)) ||
    u.host === 'collectiononline.kreml.ru' && (u.pathname === '/terms-of-use' || /^\/entity\/OBJECT(?:\/\d+)?$/.test(u.pathname)) &&
      [...u.searchParams.keys()].every(k=>k==='rubrics') ||
    u.host === 'ikonen-museum.com' && u.pathname === '/en/ikonen-museum/sammlung' && !u.search;
  if(!permitted)throw Error('Outside reviewed metadata routes; no API, image or arbitrary page downloads');
  await mkdir(out,{recursive:true,mode:0o700});
  const file = sha(url)+'.html';
  try {
    const receipt=JSON.parse(await readFile(join(out,file+'.snapshot.json'))), b=await readFile(join(out,file));
    if(receipt.url!==url || receipt.sha256!==sha(b) || receipt.bytes!==b.length) throw Error('Capture changed');
    return {...extract(b.toString(),url),snapshot:receipt};
  } catch(e) {if(e.code!=='ENOENT') throw e;}
  await pause(10500);
  const r=await fetch(url,{redirect:'manual',signal:AbortSignal.timeout(35000),headers:{'User-Agent':'ArtlineMuseumResearch/1.0 (selected factual metadata; no images)','Accept':'text/html,text/plain'}});
  if(r.status!==200) throw Error(`${r.status} ${url}; stopped without retry`);
  const chunks=[];let size=0;
  for await(const b of r.body){size+=b.length;if(size>2*1024*1024)throw Error('Page exceeds 2MiB');chunks.push(b);}
  const b=Buffer.concat(chunks), receipt={url,sha256:sha(b),bytes:b.length,retrieved_at:new Date().toISOString()};
  await writeFile(join(out,file),b,{flag:'wx',mode:0o600});
  await writeFile(join(out,file+'.snapshot.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx',mode:0o600});
  return {...extract(b.toString(),url),snapshot:receipt};
}
if(process.argv[1]===fileURLToPath(import.meta.url)) {
  const urls=process.argv.slice(2);if(!urls.length || urls.length>30)throw Error('Supply 1–30 reviewed URLs');
  for(const url of urls) { const x=await capture(url); console.log(JSON.stringify({url,headings:x.headings,snapshot:x.snapshot})); }
}
