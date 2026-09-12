import {execFileSync} from 'node:child_process';
import {readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const root=fileURLToPath(new URL('../',import.meta.url));
const phase=process.argv[2];assert.ok(['before','preview','after','replay'].includes(phase));
const sql=q=>JSON.parse(execFileSync('psql',['postgres://localhost/artline?sslmode=disable','-XAt','-v','ON_ERROR_STOP=1','-c',q],{encoding:'utf8',maxBuffer:16*1024*1024}));
const counts=sql(`SELECT jsonb_build_object('artworks',(SELECT count(*) FROM artworks),'artists',(SELECT count(*) FROM artists),'institutions',(SELECT count(*) FROM institutions),'media',(SELECT count(*) FROM media_assets),'published',(SELECT count(*) FROM artworks WHERE status='published'),'display',(SELECT count(*) FROM artwork_location_assertions WHERE claim_type='display'))`);
const fingerprints={};
for(const table of ['artworks','artists','artwork_artists','artwork_location_assertions','external_identifiers','citations','institutions','media_assets','media_rights_evidence','curated_collection_items','import_jobs']){
 fingerprints[table]=sql(`SELECT to_jsonb(md5(string_agg(h,'' ORDER BY h))) FROM (SELECT md5(to_jsonb(t)::text) h FROM ${table} t) q`);
}
const originalWorks=sql(`SELECT to_jsonb(md5(string_agg(h,'' ORDER BY h))) FROM (SELECT md5(to_jsonb(t)::text) h FROM artworks t WHERE NOT EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=t.id AND e.scheme IN ('european-icons-athens-object','european-icons-kremlin-object'))) q`);
const result={phase,checked_at:new Date().toISOString(),counts,fingerprints,originalWorks};
const load=p=>JSON.parse(readFileSync(root+`output/icons-${p}-verification.json`));
if(phase==='preview')assert.deepEqual(fingerprints,load('before').fingerprints);
if(['after','replay'].includes(phase)){
 const before=load('before');assert.equal(originalWorks,before.originalWorks);
 for(const k of ['artists','media','published','display'])assert.equal(counts[k],before.counts[k],k);
 for(const k of ['artists','media_assets','media_rights_evidence','curated_collection_items'])assert.equal(fingerprints[k],before.fingerprints[k],k);
 assert.equal(counts.artworks-before.counts.artworks,22);assert.equal(counts.institutions-before.counts.institutions,2);
 result.policy=sql(`SELECT jsonb_build_object('total',count(*),'unlinked',count(*) FILTER(WHERE unlinked_creator_label IS NOT NULL),'eligible',count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible'),'review',count(*) FILTER(WHERE status='review'),'images',count(primary_media_id)) FROM artworks WHERE object_form='icon'`);
 assert.deepEqual(result.policy,{total:22,unlinked:21,eligible:22,review:22,images:0});
 if(phase==='replay')assert.deepEqual(fingerprints,load('after').fingerprints);
}
writeFileSync(root+`output/icons-${phase}-verification.json`,JSON.stringify(result,null,2)+'\n',{flag:'wx',mode:0o600});
console.log({phase,counts,policy:result.policy});
