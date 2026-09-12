// Museum metadata only. Public pages, no image downloads, no DB writes.
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {parse} from '../apps/web/node_modules/parse5/dist/index.js';
import {setTimeout as pause} from 'node:timers/promises';
import {execFileSync} from 'node:child_process';
export const dir='content/imports/popular-marmottan-20260911';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const clean=s=>s.replace(/\s+/g,' ').trim();
const attr=(n,k)=>n?.attrs?.find(a=>a.name===k)?.value||'';
const has=(n,c)=>attr(n,'class').split(/\s+/).includes(c);
const nodes=(n,p)=>[...(p(n)?[n]:[]),...(n.childNodes||[]).flatMap(c=>nodes(c,p))];
const text=n=>n.nodeName==='#text'?n.value:n.tagName==='br'?'\n':['script','style'].includes(n.tagName)||has(n,'MMM_BLOC_TEXT_EXCERPT')?'':(n.childNodes||[]).map(text).join('');
let last=0;
async function save(file,data){await fs.writeFile(dir+'/'+file,typeof data==='string'||Buffer.isBuffer(data)?data:JSON.stringify(data,null,2)+'\n',{flag:'wx',mode:0o600});}
export async function capture(url,author=''){
  const u=new URL(url);
  if(u.origin!=='https://www.marmottan.fr'||u.username||u.hash||u.search||!(/^\/(robots\.txt|mentions-legales\/|commandes-photos\/|collection-en-ligne\/|collections\/[^/]+\/|notice\/[A-Za-z0-9._-]+\/|recherche-collection\/)$/.test(u.pathname)||author&&u.pathname==='/wp-admin/admin-ajax.php'))throw Error('Outside public collection scope: '+url);
  const body=author?new URLSearchParams({action:'get_ajax_collection',auteur:author}).toString():'';
  const file=hash(url+body)+'.html';
  try {const raw=await fs.readFile(dir+'/'+file),snapshot=JSON.parse(await fs.readFile(dir+'/'+file+'.snapshot.json'));if(snapshot.url!==url||snapshot.sha256!==hash(raw)||(snapshot.body||'')!==body)throw Error('Changed capture');return {raw:raw.toString(),file,snapshot};}catch(e){if(e.code!=='ENOENT')throw e;}
  await pause(Math.max(0,1500-(Date.now()-last)));last=Date.now();
  const r=await fetch(url,{method:body?'POST':'GET',...(body?{body}:{}),redirect:'manual',signal:AbortSignal.timeout(35000),headers:{'User-Agent':'ArtlineResearch/1.0 (selected public museum metadata; no images)',Accept:'text/html,text/plain',...(body?{'Content-Type':'application/x-www-form-urlencoded'}:{})}});
  if(r.status!==200)throw Error(`Source paused: HTTP ${r.status} ${url}; no retries`);
  const chunks=[];let size=0;for await(const c of r.body){size+=c.length;if(size>2*1024*1024)throw Error('Page byte ceiling');chunks.push(c);}
  const b=Buffer.concat(chunks),snapshot={url,...(body?{method:'POST',body,meaning:'Read-only public artist search, exposed in museum collection page'}:{}),sha256:hash(b),bytes:size,retrieved_at:new Date().toISOString()};
  await save(file,b);await save(file+'.snapshot.json',snapshot);console.log(`${url} ${size} bytes`);
  return {raw:b.toString(),file,snapshot};
}
export function extract(raw,url){
  const doc=parse(raw),sections=nodes(doc,n=>has(n,'MMM_BLOC_NOTICE'));
  if(sections.length!==1)throw Error('Notice layout changed');
  const section=sections[0],caption=nodes(section,n=>has(n,'MMM_BLOC_TEXT'))[0];
  const headings=nodes(caption,n=>has(n,'MMM_BLOC_TEXT_SURTITLE'));
  if(headings.length!==1)throw Error('Ambiguous caption');
  const title=clean(text(nodes(headings[0],n=>n.tagName==='strong')[0]||{}));
  const lines=text(caption).split('\n').map(clean).filter(Boolean);
  const visual=nodes(section,n=>has(n,'MMM_BLOC_VISUAL'))[0];
  return {url,title,lines,image_url:attr(visual,'style').match(/url\(['"]?([^'")]+)["']?\)/)?.[1]||'',canonical:attr(nodes(doc,n=>n.tagName==='link'&&attr(n,'rel')==='canonical')[0],'href')};
}
async function run(){
  await fs.mkdir(dir,{recursive:true,mode:0o700});
  const robots=await capture('https://www.marmottan.fr/robots.txt');
  if(/^Disallow:\s*\/\s*$/mi.test(robots.raw))throw Error('Robots prohibits crawl');
  await capture('https://www.marmottan.fr/mentions-legales/');
  if(process.argv[2]==='capture'){for(const url of process.argv.slice(3))await capture(url);return;}
  const selected=new Map(),indexes=[];
  if(process.argv[2]==='popular-notices'){
    const discovery=JSON.parse(await fs.readFile(dir+'/popular-discovery-v2.json'));
    if(discovery.candidates.length<1||discovery.candidates.length>500)throw Error('Notice budget exceeded');
    const works=[];
    for(const {url,artist} of discovery.candidates){const p=await capture(url);works.push({...extract(p.raw,url),discovery_artist:artist,snapshot_file:p.file,snapshot:p.snapshot});}
    await save('popular-facts.json',{indexes:discovery.indexes,works,scope:'All object links returned for 18 exact-name popular-artist searches; source dates, attribution, medium and identity still gated in Go',images_downloaded:0});
    console.log('Captured '+works.length+' popular artist object notices.');return;
  }
  if(process.argv[2]==='popular'){
    const index=await capture('https://www.marmottan.fr/collection-en-ligne/');
    if(!index.raw.includes("action : 'get_ajax_collection'")||!index.raw.includes("auteur : sf_auteur"))throw Error('Public search contract changed');
    const popular=JSON.parse(execFileSync('psql',['postgres://localhost/artline?sslmode=disable','-XAt','-v','ON_ERROR_STOP=1','-c',`SELECT json_agg(t) FROM (SELECT a.id,a.display_name,a.sort_name,coalesce((SELECT json_agg(alias) FROM artist_aliases WHERE artist_id=a.id),'[]') AS aliases FROM artists a JOIN artist_discovery_selection d ON d.artist_id=a.id AND d.is_popular WHERE a.status<>'archived' ORDER BY a.display_name) t`],{encoding:'utf8'}));
    const key=s=>s.normalize('NFD').replace(/\p{M}/gu,'').toLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').trim().split(/\s+/).sort().join(' ');
    const names=new Set(popular.flatMap(a=>[a.display_name,a.sort_name,...a.aliases]).filter(Boolean).map(key));
    const labels=[...new Set(nodes(parse(index.raw),n=>Boolean(attr(n,'data-artist'))).map(n=>attr(n,'data-artist')))].filter(n=>names.has(key(n))).sort((a,b)=>(a==='MONET Claude'?-1:b==='MONET Claude'?1:a.localeCompare(b)));
    if(labels.length<1||labels.length>100)throw Error('Artist discovery scope changed');
    for(const author of labels){
      const page=await capture('https://www.marmottan.fr/wp-admin/admin-ajax.php',author);indexes.push({...page.snapshot,author});
      for(const n of nodes(parse(page.raw),n=>n.tagName==='a')){
        const href=attr(n,'href');if(!href)continue;
        const u=new URL(href,'https://www.marmottan.fr');if(!/^\/notice\/[A-Za-z0-9._-]+\/$/.test(u.pathname)||u.search!=='?is=true')continue;
        u.search='';selected.set(u.href,author);
      }
    }
    await save('popular-discovery-v2.json',{popular,matched_source_artists:labels,indexes,candidates:[...selected].map(([url,artist])=>({url,artist})),scope:'Exact artist-name/alias discovery against the public museum A–Z catalogue; final authority validation in Go. Corrected canonicalization of public ?is=true display links; initial zero-candidate parser output is not a museum absence claim.'});
    console.log('Popular discovery: '+labels.length+' source artists, '+selected.size+' object notices.');
    return;
  }
  for(const slug of ['claude-monet','berthe-morisot','impressionnisme-et-temps-modernes']){
    const page=await capture('https://www.marmottan.fr/collections/'+slug+'/');indexes.push(page.snapshot);
    for(const n of nodes(parse(page.raw),n=>n.tagName==='a')){
      const href=attr(n,'href');if(!/\/notice\/[^/]+\/?$/.test(href))continue;
      const u=new URL(href,'https://www.marmottan.fr');if(!u.pathname.endsWith('/'))u.pathname+='/';
      selected.set(u.href,clean(text(n)));
    }
  }
  if(selected.size<1||selected.size>150)throw Error('Unexpected selection size');
  const works=[];
  for(const [url,label] of selected){const p=await capture(url);works.push({...extract(p.raw,url),label,snapshot_file:p.file,snapshot:p.snapshot});}
  await save('facts.json',{indexes,works,scope:'All notice links from the three named collection indexes, not the entire museum; Go filters current popular artists',images_downloaded:0});
  console.log('Captured '+works.length+' exact object captions.');
}
if(process.argv[1]?.endsWith('/research-popular-marmottan.mjs'))await run();
