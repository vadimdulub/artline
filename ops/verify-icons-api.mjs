import {readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const root=fileURLToPath(new URL('../',import.meta.url));
const token=readFileSync(root+'apps/server/.env','utf8').match(/^ARTLINE_EDITOR_TOKEN=(.*)$/m)[1].trim().replace(/^(['"])(.*)\1$/,'$2');
const requests=[];
async function get(path,auth=true,status=200){const started=performance.now();const r=await fetch('http://localhost:8080/api/v1/'+path,{headers:auth?{Authorization:'Bearer '+token}:{},signal:AbortSignal.timeout(12000)});requests.push({path,status:r.status,ms:Math.round(performance.now()-started)});assert.equal(r.status,status,path);return r.json();}
for(const[slug,total]of [['byzantine-christian-museum-athens',15],['moscow-kremlin-museums',7]]){
 const m=await get(`museums/${slug}?preview=1`);assert.equal(m.work_count,total);assert.equal(m.on_view_count,0);assert.equal(m.highlight_count,0);
 let cursor='',seen=new Set();do {const p=await get(`museums/${slug}/works?preview=1&limit=5${cursor?'&cursor='+encodeURIComponent(cursor):''}`);assert.equal(p.total,total);assert.ok(p.items.length<=5);for(const w of p.items){assert.ok(!seen.has(w.id));seen.add(w.id);assert.equal(w.object_form,'icon');assert.ok(w.artists.length||w.unlinked_creator_label);assert.equal(w.media_url,null);assert.equal(w.display,null);}cursor=p.next_cursor;}while(cursor);
 assert.equal(seen.size,total);
 const detail=await get(`museums/${slug}/works/${[...seen][0]}?preview=1`);assert.ok(detail.citations.length);assert.ok(detail.description_md);assert.ok(detail.cultural_context);
 assert.equal((await get(`museums/${slug}/works?preview=1&display=on_view`)).total,0);
 assert.equal((await get(`museums/${slug}/works?preview=1&artist=claude-monet&artist=camille-pissarro-q134741`)).total,0);
 await get(`museums/${slug}`,false,404);await get(`museums/${slug}?preview=1`,false,401);
}
const g=await get('museums/byzantine-christian-museum-athens/works?preview=1&q=Constantinople');assert.ok(g.total>=3);assert.ok(g.items.every(w=>w.unlinked_creator_label.includes('Constantinople')));
const p=await get('museums/moscow-kremlin-museums/works?preview=1&artist=theophanes-the-greek-q319403');assert.equal(p.total,1);assert.equal(p.items[0].artists[0].role,'attributed_to');
const d=await get(`museums/moscow-kremlin-museums/works/${p.items[0].id}?preview=1`);assert.equal(d.creation_year_start,1376);assert.equal(d.creation_year_end,1400);assert.equal(d.attribution_role,'attributed_to');
await get('artists/theophanes-the-greek-q319403/works?preview=1&limit=5');
const translated=await get('museums/moscow-kremlin-museums/works?preview=1&q=Mother%20of%20God');assert.equal(translated.total,7);
const directory=await get('museums?preview=1&q=Byzantine%20and%20Christian');assert.equal(directory.total,1);assert.equal(directory.items[0].work_count,15);
await get('museums?preview=1&limit=24');
writeFileSync(root+'output/icons-api-verification-v2.json',JSON.stringify({checked_at:new Date().toISOString(),requests,limitation:'Bounded local HTTP checks, not a production-scale benchmark'},null,2)+'\n',{flag:'wx',mode:0o600});
console.log(`${requests.length} API checks passed; max ${Math.max(...requests.map(r=>r.ms))}ms`);
