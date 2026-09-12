// Read-only fingerprints / API checks. Receipts are immutable and contain no tokens.
import {readFileSync,writeFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const mode=process.argv[2];
assert(['before','preview','applied','replay','api'].includes(mode),'Choose verification phase');
const sql=q=>JSON.parse(execFileSync('psql',['postgres://localhost/artline?sslmode=disable','-X','-At','-v','ON_ERROR_STOP=1','-c',q],{encoding:'utf8',maxBuffer:8*1024*1024}));
const tables=['artists','artworks','institutions','citations','external_identifiers','artwork_artists','artwork_location_assertions','media_assets','media_rights_evidence','curated_collections','curated_collection_items','audit_log','import_jobs','import_records'];
const read=phase=>JSON.parse(readFileSync(path.join(root,`output/continuation-${phase}-verification.json`),'utf8'));
let result={phase:mode,checked_at:new Date().toISOString()};
if(mode!=='api'){
 result.fingerprints=Object.fromEntries(tables.map(t=>[t,sql(`SELECT jsonb_build_object('count',count(*),'fingerprint',md5(coalesce(string_agg(md5(to_jsonb(t)::text),'' ORDER BY md5(to_jsonb(t)::text)),''))) FROM public.${t} t`)]));
 result.counts=sql(`SELECT jsonb_build_object('artworks',(SELECT count(*) FROM artworks),'artists',(SELECT count(*) FROM artists),'institutions',(SELECT count(*) FROM institutions),'media',(SELECT count(*) FROM media_assets),'published',(SELECT count(*) FROM artworks WHERE published_at IS NOT NULL OR status='published'),'display',(SELECT count(*) FROM artwork_location_assertions WHERE claim_type='display'))`);
 result.types=sql(`SELECT jsonb_object_agg(work_type,n) FROM (SELECT work_type,count(*) n FROM artworks GROUP BY 1) x`);
 if(mode==='preview')assert.deepEqual(result.fingerprints,read('before').fingerprints,'Preview changed persistent rows');
 if(mode==='replay')assert.deepEqual(result.fingerprints,read('applied').fingerprints,'Replay changed persistent rows');
 if(mode==='applied'||mode==='replay'){
  result.invalid=sql(`SELECT count(DISTINCT a.id) FROM artworks a JOIN import_records r ON r.matched_entity_id=a.id JOIN import_jobs j ON j.id=r.import_job_id WHERE j.idempotency_key LIKE 'continuation-%' AND (a.status<>'review' OR a.published_at IS NOT NULL OR artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)<>'eligible' OR coalesce(a.description_md,'')='')`);assert.equal(result.invalid,0);assert.equal(result.counts.published,0);assert.equal(result.counts.display,0);
  result.receipts=sql(`SELECT jsonb_agg(x) FROM (SELECT s.slug,count(DISTINCT j.id) jobs,count(*) records,count(*) FILTER(WHERE r.outcome='created' AND r.matched_entity_type='artwork') created FROM import_jobs j JOIN sources s ON s.id=j.source_id JOIN import_records r ON r.import_job_id=j.id WHERE j.idempotency_key LIKE 'continuation-%' GROUP BY s.slug) x`);
 }
}else{
 const token=readFileSync(path.join(root,'apps/server/.env'),'utf8').match(/^ARTLINE_EDITOR_TOKEN=(.*)$/m)[1].trim().replace(/^(['"])(.*)\1$/,'$2');result.requests=[];
 async function get(route,auth=true){const start=performance.now();const response=await fetch('http://localhost:8080/api/v1/'+route,{headers:auth?{Authorization:'Bearer '+token}:{},signal:AbortSignal.timeout(30000)});const data=await response.json();result.requests.push({route,status:response.status,ms:Math.round(performance.now()-start)});return {status:response.status,data};}
 for(const slug of ['pushkin-state-museum-fine-arts','accademia-brera-collections','castello-sforzesco-graphic-collections','joconde-m5041','joconde-m0607']){
  const expected=sql(`SELECT count(*) FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE i.slug='${slug}'`);
  const museum=await get(`museums/${slug}?preview=1`);assert.equal(museum.status,200);assert.equal(museum.data.work_count,expected);assert.equal(museum.data.on_view_count,0);
  const page=await get(`museums/${slug}/works?preview=1&limit=5`);assert.equal(page.status,200);assert.equal(page.data.items.length,5);assert(page.data.next_cursor);
  const next=await get(`museums/${slug}/works?preview=1&limit=5&cursor=${encodeURIComponent(page.data.next_cursor)}`);assert.equal(next.status,200);assert(next.data.items.every(x=>!page.data.items.some(y=>y.id===x.id)));
  const detail=await get(`museums/${slug}/works/${page.data.items[0].id}?preview=1`);assert.equal(detail.status,200);assert(detail.data.description_md);
 }
 for(const slug of ['claude-monet','camille-pissarro-q134741','francesco-hayez-q223725']){const page=await get(`artists/${slug}/works?preview=1&limit=5`);assert.equal(page.status,200);assert(page.data.items.length<=5);assert(page.data.items.every(w=>w.description_md===undefined));}
 const f=await get('museums/pushkin-state-museum-fine-arts/works?preview=1&limit=50&artist=claude-monet&artist=camille-pissarro-q134741');assert.equal(f.status,200);assert(f.data.items.length>0);assert(f.data.items.every(w=>w.artists.some(a=>['claude-monet','camille-pissarro-q134741'].includes(a.slug))));
 assert.equal((await get('museums/joconde-m5041?preview=1',false)).status,401);assert.equal((await get('museums/joconde-m5041',false)).status,404);
 result.note='Single local request observations, not production/concurrency/10-million-row benchmarks.';
}
writeFileSync(path.join(root,`output/continuation-${mode}-verification.json`),JSON.stringify(result,null,2)+'\n',{flag:'wx',mode:0o600});
console.log(JSON.stringify(result));
