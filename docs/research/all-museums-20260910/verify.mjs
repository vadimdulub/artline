// Local read-only SQL fingerprints and bounded API regression checks.
import {readFileSync,writeFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const [mode,phase='initial']=process.argv.slice(2);
const receiptSuffix=process.argv[4]||'';assert(['','-v2'].includes(receiptSuffix));
assert(['before','preview','applied','replay','api'].includes(mode));
assert(['initial','chicago','final'].includes(phase));
const sql=q=>JSON.parse(execFileSync('psql',['postgres://localhost/artline?sslmode=disable','-X','-At','-v','ON_ERROR_STOP=1','-c',q],{encoding:'utf8',maxBuffer:10<<20}));
const tables=['artists','artist_aliases','artworks','institutions','citations','external_identifiers','artwork_artists','artwork_location_assertions','media_assets','media_rights_evidence','curated_collections','curated_collection_items','audit_log','import_jobs','import_records'];
const filename=m=>path.join(root,`output/campaign-${phase}-${m}${m===mode?receiptSuffix:''}-verification.json`);
const read=m=>JSON.parse(readFileSync(filename(m),'utf8'));
const result={phase,mode,checked_at:new Date().toISOString()};
if(mode!=='api'){
 result.fingerprints=Object.fromEntries(tables.map(t=>[t,sql(`SELECT jsonb_build_object('count',count(*),'fingerprint',md5(coalesce(string_agg(md5(to_jsonb(t)::text),'' ORDER BY md5(to_jsonb(t)::text)),''))) FROM public.${t} t`)]));
 result.counts=sql(`SELECT jsonb_build_object('artworks',(SELECT count(*) FROM artworks),'artists',(SELECT count(*) FROM artists),'institutions',(SELECT count(*) FROM institutions),'media',(SELECT count(*) FROM media_assets),'published',(SELECT count(*) FROM artworks WHERE published_at IS NOT NULL OR status='published'),'display',(SELECT count(*) FROM artwork_location_assertions WHERE claim_type='display'))`);
 result.types=sql(`SELECT jsonb_object_agg(work_type,n) FROM (SELECT work_type,count(*) n FROM artworks GROUP BY 1) x`);
 result.creation_scope=sql(`SELECT jsonb_object_agg(scope,n) FROM (SELECT artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,count(*) n FROM artworks GROUP BY 1) x`);
 if(mode==='preview')assert.deepEqual(result.fingerprints,read('before').fingerprints,'Preview changed rows');
 if(mode==='replay')assert.deepEqual(result.fingerprints,read('applied').fingerprints,'Replay changed rows');
 if(mode==='applied'||mode==='replay'){
  for(const table of ['artists','artist_aliases','media_assets','media_rights_evidence','curated_collection_items'])assert.deepEqual(result.fingerprints[table],read('before').fingerprints[table],`Unexpected change in ${table}`);
  result.invalid=sql(`SELECT count(DISTINCT a.id) FROM artworks a JOIN import_records r ON r.matched_entity_id=a.id AND r.matched_entity_type='artwork' JOIN import_jobs j ON j.id=r.import_job_id WHERE j.idempotency_key ~ '^continuation-(met|cleveland|lombardia|chicago)-' AND r.outcome='created' AND (a.status<>'review' OR a.published_at IS NOT NULL OR artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)<>'eligible' OR coalesce(a.description_md,'')='')`);
  assert.equal(result.invalid,0);assert.equal(result.counts.published,0);assert.equal(result.counts.display,0);
  result.source_results=sql(`SELECT coalesce(jsonb_agg(x),'[]') FROM (SELECT s.slug,count(DISTINCT j.id) jobs,count(*) FILTER(WHERE r.outcome='created' AND r.matched_entity_type='artwork') created FROM import_jobs j JOIN sources s ON s.id=j.source_id JOIN import_records r ON r.import_job_id=j.id WHERE j.idempotency_key ~ '^continuation-(met|cleveland|lombardia|chicago)-' GROUP BY s.slug) x`);
 }
}else{
 const token=readFileSync(path.join(root,'apps/server/.env'),'utf8').match(/^ARTLINE_EDITOR_TOKEN=(.*)$/m)[1].trim().replace(/^(['"])(.*)\1$/,'$2');result.requests=[];
 async function get(route,auth=true){const t=performance.now();const r=await fetch('http://localhost:8080/api/v1/'+route,{headers:auth?{Authorization:'Bearer '+token}:{},signal:AbortSignal.timeout(30000)});const d=await r.json();result.requests.push({route,status:r.status,ms:Math.round(performance.now()-t)});return {status:r.status,data:d};}
 for(const slug of ['the-met','cleveland-museum-of-art','art-institute-of-chicago','accademia-carrara','musei-civici-arte-storia-brescia']){
  const expected=sql(`SELECT count(*) FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE i.slug='${slug}'`);
  const m=await get(`museums/${slug}?preview=1`);assert.equal(m.status,200);assert.equal(m.data.work_count,expected);assert.equal(m.data.on_view_count,0);
  const p=await get(`museums/${slug}/works?preview=1&limit=5`);assert.equal(p.status,200);assert.equal(p.data.items.length,Math.min(5,expected));
  if(p.data.next_cursor){const n=await get(`museums/${slug}/works?preview=1&limit=5&cursor=${encodeURIComponent(p.data.next_cursor)}`);assert.equal(n.status,200);assert(n.data.items.every(w=>!p.data.items.some(x=>x.id===w.id)));}
  if(p.data.items.length){
   const id=p.data.items[0].id;assert(/^[a-f0-9-]{36}$/.test(id));
   const stored=sql(`SELECT jsonb_build_object('description_md',description_md) FROM artworks WHERE id='${id}'`);
   const d=await get(`museums/${slug}/works/${id}?preview=1`);assert.equal(d.status,200);
   // Earlier owner/seed records can intentionally have no description. Test
   // exact API/DB agreement, then explicitly exercise a newly imported work.
   assert.equal(d.data.description_md??null,stored.description_md);
  }
  const created=sql(`SELECT jsonb_build_object('id',a.id,'description_md',a.description_md) FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE i.slug='${slug}' AND EXISTS(SELECT 1 FROM import_records r JOIN import_jobs j ON j.id=r.import_job_id WHERE r.matched_entity_id=a.id AND r.matched_entity_type='artwork' AND r.outcome='created' AND j.idempotency_key ~ '^continuation-(met|cleveland|lombardia|chicago)-') LIMIT 1`);
  assert(created.description_md);const detail=await get(`museums/${slug}/works/${created.id}?preview=1`);assert.equal(detail.status,200);assert.equal(detail.data.description_md,created.description_md);
 }
 const licensed=sql(`SELECT jsonb_build_object('id',a.id,'description_md',a.description_md) FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE i.slug='art-institute-of-chicago' AND a.description_md LIKE '%CC BY 4.0%' LIMIT 1`);
 const licensedDetail=await get(`museums/art-institute-of-chicago/works/${licensed.id}?preview=1`);assert.equal(licensedDetail.status,200);assert.equal(licensedDetail.data.description_md,licensed.description_md);assert(licensedDetail.data.description_md.includes('https://creativecommons.org/licenses/by/4.0/'));
 for(const slug of ['claude-monet','camille-pissarro-q134741']){const p=await get(`artists/${slug}/works?preview=1&limit=5`);assert.equal(p.status,200);assert(p.data.items.length<=5);assert(p.data.items.every(w=>w.description_md===undefined));}
 const p=await get('museums/the-met/works?preview=1&limit=50&artist=claude-monet&artist=camille-pissarro-q134741');assert.equal(p.status,200);assert(p.data.items.length>0);assert(p.data.items.every(w=>w.artists.some(a=>['claude-monet','camille-pissarro-q134741'].includes(a.slug))));
 assert.equal((await get('museums/the-met?preview=1',false)).status,401);
 assert.equal((await get('museums/accademia-carrara',false)).status,404);
 result.limitations='Single local requests, not browser QA or a concurrent 10-million-row benchmark.';
}
writeFileSync(filename(mode),JSON.stringify(result,null,2)+'\n',{flag:'wx',mode:0o600});
console.log(JSON.stringify({mode,phase,counts:result.counts,creation_scope:result.creation_scope,invalid:result.invalid,source_results:result.source_results,requests:result.requests?.length}));
