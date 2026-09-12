// Local verification + replay only. No downloads, publication or remote DB.
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const output=path.join(root,'output/russia-italy-verification.json');
assert(!existsSync(output),'Verification receipt already exists');
const sql=q=>JSON.parse(execFileSync('psql',['postgres://localhost/artline?sslmode=disable','-X','-At','-v','ON_ERROR_STOP=1','-c',q],{encoding:'utf8'}));
const read=p=>JSON.parse(readFileSync(path.join(root,p),'utf8'));
const tables=['artists','artworks','institutions','citations','external_identifiers','artwork_artists','artwork_location_assertions','media_assets','media_rights_evidence','curated_collections','curated_collection_items','audit_log','import_jobs','import_records'];
const fingerprints=()=>Object.fromEntries(tables.map(t=>[t,sql(`SELECT jsonb_build_object('count',count(*),'fingerprint',md5(coalesce(string_agg(md5(to_jsonb(t)::text),'' ORDER BY md5(to_jsonb(t)::text)),''))) FROM public.${t} t`)]));
const before=fingerprints();
console.log('Captured local baseline for replay verification');
const run=args=>execFileSync('go',['run',...args],{cwd:path.join(root,'apps/server'),env:{...process.env,DATABASE_URL:'postgres://localhost/artline?sslmode=disable'},encoding:'utf8',maxBuffer:8*1024*1024});
run(['./cmd/ingest-bulk','-dir','../../docs/research/russia-italy-scale/nga-v3','-reports','../../output/nga-bulk-replay-v3','-apply']);
const manifest=read('docs/research/russia-italy-scale/nga-v3/manifest.json');
for(const c of manifest.chunks){const r=read('output/nga-bulk-replay-v3/'+c.file);assert(r.replayed&&r.created_artworks===0&&r.created_artists===0);}
for(const batch of ['pushkin-v1','brera-v1','nga-v1']){
 const file=`../../output/${batch}-final-replay.json`;
 run(['./cmd/ingest-european','-batch',batch,'-apply','-report',file]);
 const r=read(file.replace('../../',''));
 assert.equal(r.created_artworks,0);assert.equal(r.added_citations,0);assert.equal(r.enriched_existing_artworks,0);assert.equal(r.added_museum_highlights,0);
}
const after=fingerprints();
assert.deepEqual(after,before,'Replay changed persistent rows');
console.log('All 34 NGA chunks and three reviewed catalogue replays are unchanged');
const types=sql(`SELECT jsonb_object_agg(work_type,n) FROM (SELECT work_type,count(*) n FROM artworks GROUP BY 1) x`);
const unsafe=sql(`SELECT count(DISTINCT a.id) FROM artworks a JOIN import_records r ON r.matched_entity_id=a.id JOIN import_jobs j ON j.id=r.import_job_id WHERE (j.idempotency_key LIKE 'bulk-nga-%' OR j.idempotency_key IN ('pushkin-highlights-2026-09-09-v1','brera-catalogue-2026-09-09-v1')) AND (a.status<>'review' OR a.published_at IS NOT NULL OR artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)<>'eligible' OR coalesce(a.description_md,'')='')`);
assert.equal(unsafe,0);
const counts=sql(`SELECT jsonb_build_object('artworks',(SELECT count(*) FROM artworks),'artists',(SELECT count(*) FROM artists),'active_artists',(SELECT count(*) FROM artists WHERE status<>'archived'),'institutions',(SELECT count(*) FROM institutions),'media_assets',(SELECT count(*) FROM media_assets),'published_artworks',(SELECT count(*) FROM artworks WHERE status='published' OR published_at IS NOT NULL),'display_assertions',(SELECT count(*) FROM artwork_location_assertions WHERE claim_type='display'),'nga_source_identities',(SELECT count(*) FROM external_identifiers WHERE entity_type='artwork' AND scheme='european-nga-object'))`);
assert.equal(counts.artworks,34264);assert.equal(counts.nga_source_identities,33493);assert.equal(counts.published_artworks,0);assert.equal(counts.display_assertions,0);
const images=read('output/nga-images-applied-v2.json');
for(const r of images.Results.filter(r=>r.Outcome==='attached')){
 const rows=sql(`SELECT jsonb_agg(jsonb_build_object('sha',m.checksum_sha256,'bytes',m.byte_size,'rights',m.rights_status,'width',m.width,'height',m.height,'evidence',e.evidence_json)) FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.storage_path='${r.Path}'`);
 assert.equal(rows.length,1);const m=rows[0];assert.equal(m.rights,'licensed');assert(m.width<=600&&m.height<=600);assert.equal(m.evidence.openaccess,'1');
 const b=readFileSync(path.join(root,'apps/web/public',r.Path));assert.equal(b.length,m.bytes);assert.equal(createHash('sha256').update(b).digest('hex'),m.sha);
}
const envText=readFileSync(path.join(root,'apps/server/.env'),'utf8');
const token=envText.match(/^ARTLINE_EDITOR_TOKEN=(.*)$/m)?.[1]?.trim().replace(/^(['"])(.*)\1$/,'$2');
assert(token,'Local editor token missing');
const api=[];
async function get(route,auth=true){
 const start=performance.now();const res=await fetch('http://localhost:8080/api/v1/'+route,{headers:auth?{Authorization:'Bearer '+token}:{},signal:AbortSignal.timeout(30000)});
 const data=await res.json();api.push({route,status:res.status,ms:Math.round(performance.now()-start)});return {status:res.status,data};
}
for(const [slug,total] of [['national-gallery-of-art',33493],['pushkin-state-museum-fine-arts',49],['pinacoteca-di-brera',13]]){
 const a=await get(`museums/${slug}?preview=1`);assert.equal(a.status,200);assert.equal(a.data.work_count,total);assert.equal(a.data.on_view_count,0);
 const first=await get(`museums/${slug}/works?preview=1&limit=5`);assert.equal(first.status,200);assert.equal(first.data.items.length,5);assert(first.data.next_cursor);
 const second=await get(`museums/${slug}/works?preview=1&limit=5&cursor=${encodeURIComponent(first.data.next_cursor)}`);assert.equal(second.status,200);assert(second.data.items.every(x=>!first.data.items.some(y=>y.id===x.id)));
}
const artists=['claude-monet','camille-pissarro-q134741'];
const f=await get('museums/national-gallery-of-art/works?preview=1&limit=50&artist='+artists.join('&artist='));
assert.equal(f.status,200);assert(f.data.items.length>0);assert(f.data.items.every(x=>x.artists.some(a=>artists.includes(a.slug))));
for(const slug of artists){const r=await get(`artists/${slug}/works?preview=1&limit=5`);assert.equal(r.status,200);assert(r.data.items.length<=5);assert(r.data.total>0);}
const mediaRow=images.Results.find(r=>r.Outcome==='attached');
const imageRes=await fetch('http://localhost:3000'+mediaRow.Path,{signal:AbortSignal.timeout(20000)});assert.equal(imageRes.status,200);assert(imageRes.headers.get('content-type')?.includes('image/jpeg'));
const denied=await get('museums/pushkin-state-museum-fine-arts?preview=1',false);assert.equal(denied.status,401);
const publicMuseum=await get('museums/pushkin-state-museum-fine-arts',false);assert.equal(publicMuseum.status,404);
const result={checked_at:new Date().toISOString(),turn_start:{artworks:2223,artists:1002,institutions:56,media_assets:211},counts,types,new_artworks:32041,new_artists:4313,new_images:19,unsafe_new_rows:unsafe,replays_unchanged:true,before_replay:before,after_replay:after,api,image_files_verified:19,image_visual_qa_sample:['41607','46005','164951'],note:'Images checked mechanically for all 19; visual review sampled. No browser UI test or 10-million-row benchmark claimed.'};
writeFileSync(output,JSON.stringify(result,null,2)+'\n',{flag:'wx',mode:0o600});
console.log(JSON.stringify({counts,types,replays_unchanged:true,new_artworks:32041,new_images:19,api}));
