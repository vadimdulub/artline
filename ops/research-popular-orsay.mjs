// Monet's public A–Z object index. Metadata only, no images or database writes.
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {parse} from '../apps/web/node_modules/parse5/dist/index.js';
import {setTimeout as pause} from 'node:timers/promises';
const dir='content/imports/popular-orsay-20260911';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const attr=(n,k)=>n.attrs?.find(a=>a.name===k)?.value||'';
const nodes=(n,p)=>[...(p(n)?[n]:[]),...(n.childNodes||[]).flatMap(c=>nodes(c,p))];
const text=n=>n.nodeName==='#text'?n.value:['script','style'].includes(n.tagName)?'':(n.childNodes||[]).map(text).join(' ');
const clean=s=>s.replace(/\s+/g,' ').trim();
await fs.mkdir(dir,{recursive:true,mode:0o700});
const pages=[],records=[],failures=[];
for(const letter of 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'){
  const url='https://www.musee-orsay.fr/en/artistes/oeuvres/127194/'+letter,file=letter+'.html';
  let b,snapshot;
  try{b=await fs.readFile(dir+'/'+file);snapshot=JSON.parse(await fs.readFile(dir+'/'+file+'.snapshot.json'));if(snapshot.url!==url||snapshot.sha256!==hash(b))throw Error('Changed capture');}
  catch(e){
    if(e.code!=='ENOENT')throw e;
    await pause(1800);
    const r=await fetch(url,{redirect:'manual',signal:AbortSignal.timeout(30000),headers:{'User-Agent':'ArtlineResearch/1.0 (selected public museum object facts)',Accept:'text/html'}});
    if(r.status!==200){failures.push({url,status:r.status,outcome:'Source paused; no retries or alternate-language bypass'});break;}
    const chunks=[];let size=0;for await(const c of r.body){size+=c.length;if(size>2*1024*1024)throw Error('Metadata byte cap');chunks.push(c);}
    b=Buffer.concat(chunks);snapshot={url,sha256:hash(b),bytes:b.length,retrieved_at:new Date().toISOString()};
    await fs.writeFile(dir+'/'+file,b,{flag:'wx',mode:0o600});await fs.writeFile(dir+'/'+file+'.snapshot.json',JSON.stringify(snapshot,null,2)+'\n',{flag:'wx',mode:0o600});
  }
  const doc=parse(b.toString());
  for(const row of nodes(doc,n=>n.tagName==='tr')){
    const cells=nodes(row,n=>n.tagName==='td');if(!cells.length)continue;
    const links=nodes(cells[0],n=>n.tagName==='a').map(n=>new URL(attr(n,'href'),url).href).filter(u=>/\/(artworks|oeuvres)\//.test(u));
    if(links.length!==1)continue;
    records.push({url:links[0],cells:cells.map(n=>clean(text(n))),index_url:url,snapshot_file:file,snapshot});
  }
  pages.push(snapshot);console.log(letter+': '+records.length+' cumulative object rows');
}
await fs.writeFile(dir+'/discovery.json',JSON.stringify({pages,records,failures,complete_alphabet:pages.length===26,scope:'Monet official artist A–Z index; individual custody/attribution review needed, not all records necessarily physical paintings'},null,2)+'\n',{flag:'wx',mode:0o600});
console.log(JSON.stringify({pages:pages.length,records:records.length,failures}));
