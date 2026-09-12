// Local, read-only invariant checks around the reviewed Marmottan import.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
const phase=process.argv[2]; assert(['before','after','replay'].includes(phase));
const sql=q=>JSON.parse(execFileSync('psql',['postgres://localhost/artline?sslmode=disable','-XAt','-v','ON_ERROR_STOP=1','-c',q],{encoding:'utf8',maxBuffer:100<<20}));
const read=p=>JSON.parse(fs.readFileSync(p));
const state={phase,checked_at:new Date().toISOString(),
 works:sql(`SELECT json_agg(t) FROM (SELECT id,md5(to_jsonb(a)::text) hash FROM artworks a ORDER BY id)t`),
 impression:sql(`SELECT to_jsonb(a) FROM artworks a WHERE id='b9438693-7b77-4fd2-8254-745aefa363da'`),
 hashes:Object.fromEntries(['artists','artist_discovery_selection','institutions','media_assets','media_rights_evidence','curated_collection_items'].map(table=>[table,sql(`SELECT to_json(md5(string_agg(to_jsonb(t)::text,'' ORDER BY to_jsonb(t)::text))) FROM ${table} t`)])),
};
if(phase!=='before'){
 const before=read('output/popular-metadata-before.json'),r=read('output/popular-marmottan-apply-v2/chunk-001.json');
 assert(r.applied);assert.equal(r.created_artworks,232);assert.equal(r.reused_artworks,1);assert.equal(r.added_museum_highlights,0);
 assert.equal(state.works.length-before.works.length,r.created_artworks);assert.deepEqual(state.hashes,before.hashes);
 const after=new Map(state.works.map(w=>[w.id,w.hash]));
 for(const w of before.works) if(w.id!==before.impression.id)assert.equal(after.get(w.id),w.hash,`preserved ${w.id}`);
 const allowed=new Set(['medium_text','dimensions_text','revision','updated_at','updated_by']);
 for(const [k,v]of Object.entries(before.impression))if(!allowed.has(k)||v!==null&&!['revision','updated_at','updated_by'].includes(k))assert.deepEqual(state.impression[k],v,k);
 assert.equal(state.impression.revision,before.impression.revision+1);
 const policy=sql(`SELECT jsonb_build_object('linked',count(*),'invalid',count(*) FILTER(WHERE a.status<>'review' OR artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)<>'eligible' OR NOT EXISTS(SELECT 1 FROM artwork_artists aa JOIN artist_discovery_selection d ON d.artist_id=aa.artist_id WHERE aa.artwork_id=a.id AND d.is_popular))) FROM artworks a WHERE EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme LIKE 'european-popular-marmottan%')`);
 assert.equal(policy.linked,233);assert.equal(policy.invalid,0);state.policy=policy;
 if(phase==='replay'){const previous=read('output/popular-metadata-after.json');assert.deepEqual(state.works,previous.works);assert.deepEqual(state.hashes,previous.hashes)}
}
fs.writeFileSync(`output/popular-metadata-${phase}.json`,JSON.stringify(state,null,2)+'\n',{flag:'wx',mode:0o600});
console.log(JSON.stringify({phase,artworks:state.works.length,policy:state.policy,passed:true}));
