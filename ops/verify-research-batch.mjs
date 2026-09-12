// Local read-only invariant checks for reviewed new-artwork-only research batches.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
const [phase,output,beforeFile,receiptFile]=process.argv.slice(2);
assert(['before','after','replay'].includes(phase)&&output);
const sql=q=>JSON.parse(execFileSync('psql',['-h','127.0.0.1','-d','artline','-XAt','-v','ON_ERROR_STOP=1','-c',q],{encoding:'utf8',maxBuffer:100<<20}));
const read=p=>JSON.parse(fs.readFileSync(p));
const state={phase,at:new Date().toISOString(),
 works:sql(`SELECT coalesce(json_agg(t),'[]') FROM (SELECT id,md5(to_jsonb(a)::text) hash FROM artworks a ORDER BY id)t`),
 institutions:sql(`SELECT coalesce(json_agg(t),'[]') FROM (SELECT id,slug,status,md5(to_jsonb(i)::text) hash FROM institutions i ORDER BY id)t`),
 hashes:Object.fromEntries(['artists','artist_discovery_selection','institutions','media_assets','media_rights_evidence','curated_collection_items'].map(table=>[table,sql(`SELECT to_json(md5(string_agg(to_jsonb(t)::text,'' ORDER BY to_jsonb(t)::text))) FROM ${table} t`)])),
};
if(phase!=='before'){
 const before=read(beforeFile),r=read(receiptFile);
 assert(r.applied&&r.created_artworks>0&&r.created_artworks<=500);
 assert.equal(r.reused_artworks,0);assert.equal(r.added_museum_highlights,0);
 assert(Number.isInteger(r.created_museums)&&r.created_museums>=0&&r.created_museums<=10);
 assert.equal(state.works.length-before.works.length,r.created_artworks);
 for (const [table,hash] of Object.entries(before.hashes)) {
  if(table==='institutions'&&r.created_museums>0) continue;
  assert.equal(state.hashes[table],hash,table+' preserved');
 }
 if(r.created_museums>0) {
  assert(Array.isArray(before.institutions),'new-museum verification needs a row-level baseline');
  assert.equal(state.institutions.length-before.institutions.length,r.created_museums);
  const current=new Map(state.institutions.map(i=>[i.id,i]));
  const old=new Set(before.institutions.map(i=>i.id));
  for(const i of before.institutions) assert.equal(current.get(i.id)?.hash,i.hash,'existing museum preserved');
  for(const i of state.institutions.filter(i=>!old.has(i.id))) assert.equal(i.status,'review','new museum unpublished');
 }
 const after=new Map(state.works.map(w=>[w.id,w.hash]));
 for(const w of before.works)assert.equal(after.get(w.id),w.hash,'existing artwork preserved '+w.id);
 const ids=r.works.map(w=>w.artwork_id);
 assert(ids.every(id=>/^[a-f0-9-]{36}$/.test(id)));
 const policy=sql(`SELECT jsonb_build_object('linked',count(*),'invalid',count(*) FILTER(WHERE a.status<>'review' OR a.primary_media_id IS NOT NULL OR artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)<>'eligible' OR NOT EXISTS(SELECT 1 FROM artwork_artists aa JOIN artist_discovery_selection d ON d.artist_id=aa.artist_id WHERE aa.artwork_id=a.id AND d.is_popular) OR NOT EXISTS(SELECT 1 FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.claim_type='holding' AND l.review_state='accepted'))) FROM artworks a WHERE a.id IN (${ids.map(id=>"'"+id+"'").join(',')})`);
 assert.equal(policy.linked,r.created_artworks);assert.equal(policy.invalid,0);
 state.verification={passed:true,new_artworks:r.created_artworks,new_museums:r.created_museums,policy};
}
fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(state,null,2)+'\n',{flag:'wx',mode:0o600});
console.log({phase,artworks:state.works.length,...state.verification});
