// Read-only checks against the optimized local API; keep the baseline receipt.
import {readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const token=readFileSync(path.join(root,'apps/server/.env'),'utf8').match(/^ARTLINE_EDITOR_TOKEN=(.*)$/m)[1].trim().replace(/^(['"])(.*)\1$/,'$2');
const results=[];
async function get(route,auth=true){const start=performance.now();const r=await fetch('http://localhost:8080/api/v1/'+route,{headers:auth?{Authorization:'Bearer '+token}:{},signal:AbortSignal.timeout(30000)});const d=await r.json();results.push({route,status:r.status,ms:Math.round(performance.now()-start)});return {status:r.status,data:d};}
for(const [slug,count] of [['national-gallery-of-art',33493],['pushkin-state-museum-fine-arts',49],['pinacoteca-di-brera',13]]){
 const m=await get(`museums/${slug}?preview=1`);assert.equal(m.status,200);assert.equal(m.data.work_count,count);assert.equal(m.data.on_view_count,0);
 const first=await get(`museums/${slug}/works?preview=1&limit=5`);assert.equal(first.status,200);assert.equal(first.data.items.length,5);assert(first.data.next_cursor);
 const next=await get(`museums/${slug}/works?preview=1&limit=5&cursor=${encodeURIComponent(first.data.next_cursor)}`);assert.equal(next.status,200);assert(next.data.items.every(x=>!first.data.items.some(y=>y.id===x.id)));
 const detail=await get(`museums/${slug}/works/${first.data.items[0].id}?preview=1`);assert.equal(detail.status,200);assert(detail.data.description_md);
}
const artists=['claude-monet','camille-pissarro-q134741'];
const filtered=await get('museums/national-gallery-of-art/works?preview=1&limit=50&artist='+artists.join('&artist='));assert.equal(filtered.status,200);assert(filtered.data.items.length>0);assert(filtered.data.items.every(x=>x.artists.some(a=>artists.includes(a.slug))));
for(const slug of artists){const r=await get(`artists/${slug}/works?preview=1&limit=5`);assert.equal(r.status,200);assert(r.data.items.length<=5&&r.data.total>0);assert(r.data.items.every(w=>w.description_md===undefined),'Long text leaked into chronology page');}
assert.equal((await get('museums/pushkin-state-museum-fine-arts?preview=1',false)).status,401);
assert.equal((await get('museums/pushkin-state-museum-fine-arts',false)).status,404);
const receipt={checked_at:new Date().toISOString(),results,note:'Single local observation per request, not a concurrency or production benchmark. Previous timings in russia-italy-verification.json.'};
writeFileSync(path.join(root,'output/russia-italy-api-optimized.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx',mode:0o600});
console.log(JSON.stringify(receipt));
