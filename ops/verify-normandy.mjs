// Read-only catalogue checks and bounded API probes. No account or DB mutations.
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';
const root=resolve(new URL('..',import.meta.url).pathname);
const phase=process.argv[2]; assert.ok(['before','preview','after','replay'].includes(phase));
const sql=q=>JSON.parse(execFileSync('psql',['postgres://localhost/artline?sslmode=disable','-X','-At','-v','ON_ERROR_STOP=1','-c',q],{encoding:'utf8',maxBuffer:8<<20}));
const counts=sql(`SELECT jsonb_build_object('artworks',(SELECT count(*) FROM artworks),'artists',(SELECT count(*) FROM artists),'institutions',(SELECT count(*) FROM institutions),'media',(SELECT count(*) FROM media_assets),'published',(SELECT count(*) FROM artworks WHERE status='published'),'display',(SELECT count(*) FROM artwork_location_assertions WHERE claim_type='display'))`);
const fingerprints={};
for(const table of ['artworks','artwork_artists','artwork_location_assertions','external_identifiers','citations','institutions','media_assets','media_rights_evidence','curated_collection_items','import_jobs']){
  fingerprints[table]=sql(`SELECT to_jsonb(md5(string_agg(h,'' ORDER BY h))) FROM (SELECT md5(to_jsonb(t)::text) h FROM ${table} t) q`);
}
const museums=sql(`SELECT coalesce(jsonb_agg(x ORDER BY slug),'[]'::jsonb) FROM (SELECT i.slug,i.name,p.name city,count(a.id) artworks,count(a.primary_media_id) images FROM institutions i LEFT JOIN places p ON p.id=i.place_id LEFT JOIN artworks a ON a.current_institution_id=i.id WHERE p.country_code='FR' GROUP BY i.id,p.name) x`);
const protectedWorks=sql(`SELECT jsonb_agg(x ORDER BY id) FROM (SELECT id,title,date_display,creation_year_start,creation_year_end,primary_media_id,description_md FROM artworks WHERE id IN ('f6a86903-02ba-42ed-bd78-0cfa2a780418','d3f00c41-414a-4ac7-98d1-73bc73753798','af9c2c5c-6b32-4252-aa6c-ed175a6fc03e','6fc1e60f-7212-4983-b6cc-bb1fe514c8e7','a6172ef0-3599-4053-89c6-d78bf0155e81','335f9640-7d32-45e7-a81b-83bb9246baa1')) x`);
const result={phase,checked_at:new Date().toISOString(),counts,fingerprints,museums,protectedWorks};
const load=p=>JSON.parse(readFileSync(`${root}/output/normandy-${p}-verification.json`));
if(phase==='preview'){assert.deepEqual(fingerprints,load('before').fingerprints);}
if(phase==='after'||phase==='replay'){
  const before=load('before');
  assert.deepEqual(protectedWorks,before.protectedWorks);
  for(const k of ['artists','institutions','media','published','display']) assert.equal(counts[k],before.counts[k],k);
  assert.equal(fingerprints.media_assets,before.fingerprints.media_assets);
  assert.equal(fingerprints.media_rights_evidence,before.fingerprints.media_rights_evidence);
  const receipts=[];
  for(const source of ['muma','rouen','joconde']){
    const dir=`${root}/output/normandy-${source}-apply-20260910`;
    for(const file of readdirSync(dir).filter(f=>f.endsWith('.json'))) receipts.push(JSON.parse(readFileSync(`${dir}/${file}`)));
  }
  result.created=receipts.reduce((n,r)=>n+r.created_artworks,0);
  result.reused=receipts.reduce((n,r)=>n+r.reused_artworks,0);
  result.highlights=receipts.reduce((n,r)=>n+r.added_museum_highlights,0);
  assert.equal(counts.artworks-before.counts.artworks,result.created);
  const policy=sql(`SELECT jsonb_build_object('linked',count(*),'invalid',count(*) FILTER(WHERE a.status<>'review' OR artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)<>'eligible')) FROM artworks a WHERE EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme LIKE 'european-normandy-%')`);
  assert.equal(policy.invalid,0);result.policy=policy;
  if(phase==='replay')assert.deepEqual(fingerprints,load('after').fingerprints);
}
writeFileSync(`${root}/output/normandy-${phase}-verification.json`,JSON.stringify(result,null,2)+'\n',{flag:'wx',mode:0o600});
console.log(JSON.stringify({phase,counts,created:result.created,reused:result.reused,highlights:result.highlights,policy:result.policy},null,2));
