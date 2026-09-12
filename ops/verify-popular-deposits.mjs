import fs from 'node:fs';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
const read=p=>JSON.parse(fs.readFileSync(p));
const before=read('output/popular-chicago-followup/before-metadata.json');
const receipt=read('output/popular-deposits-apply/chunk-001.json');assert(receipt.applied&&receipt.created_artworks===2&&receipt.reused_artworks===0&&receipt.created_museums===0&&receipt.added_museum_highlights===0);
const sql=q=>JSON.parse(execFileSync('psql',['postgres://localhost/artline?sslmode=disable','-XAt','-v','ON_ERROR_STOP=1','-c',q],{encoding:'utf8',maxBuffer:100<<20}));
const now=sql(`SELECT json_agg(t) FROM (SELECT id,md5(to_jsonb(a)::text) hash FROM artworks a ORDER BY id)t`);assert.equal(now.length,before.works.length+2);
const hashes=new Map(now.map(w=>[w.id,w.hash]));for(const w of before.works)assert.equal(hashes.get(w.id),w.full_hash);
const ids=receipt.works.map(w=>w.artwork_id);for(const id of ids)assert(/^[a-f0-9-]{36}$/.test(id));const excluded=ids.map(id=>`'${id}'`).join(',');
for(const [table,key,order]of [['artwork_artists','attributions_hash','a.artwork_id,a.artist_id'],['artwork_location_assertions','locations_hash','a.id']]){
 const hash=sql(`SELECT to_json(md5(string_agg(to_jsonb(a)::text,'' ORDER BY ${order}))) FROM ${table} a WHERE a.artwork_id NOT IN (${excluded})`);assert.equal(hash,before[key]);
}
const rows=sql(`SELECT json_agg(t) FROM (SELECT a.id,a.accession_number,a.date_precision,a.creation_year_start,a.creation_year_end,a.description_md,a.status FROM artworks a WHERE a.id IN (${excluded}))t`);
for(const w of rows){assert.equal(w.status,'review');assert(w.description_md.includes('depositor'));assert(w.creation_year_end<=1970)}
assert.equal(rows.find(w=>w.accession_number==='D.2018.1.12').date_precision,'exact');assert.equal(rows.find(w=>w.accession_number==='D.2018.1.14').date_precision,'circa');
fs.writeFileSync('output/popular-deposits-verification.json',JSON.stringify({passed:true,checked_at:new Date().toISOString(),created:2,prior_artworks_preserved:before.works.length,rows},null,2)+'\n',{flag:'wx',mode:0o600});console.log('Two deposits verified; every prior artwork and prior attribution/holding preserved.');
