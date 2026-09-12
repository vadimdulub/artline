import fs from 'node:fs';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';

const output=process.argv[2];assert(output&&!fs.existsSync(output));
const dir='output/popular-nationalmuseum-followup';
const before=JSON.parse(fs.readFileSync(`${dir}/before.json`));
const after=JSON.parse(fs.readFileSync(`${dir}/after.json`));
const receipt=JSON.parse(fs.readFileSync(`${dir}/date-apply.json`));
const id='2c50d912-d5c0-45c3-aad0-cd3bbf300e7a';
assert.equal(receipt.artwork_id,id);assert.equal(receipt.applied,true);
for(const key of ['artists_hash','attributions_hash','locations_hash','media','selections'])assert.deepEqual(after[key],before[key],key);
assert.equal(after.works.length,before.works.length);
const old=new Map(before.works.map(w=>[w.id,w]));
for(const w of after.works){if(w.id!==id)assert.deepEqual(w,old.get(w.id),'non-target unchanged');else assert.equal(w.revision,old.get(id).revision+1);}
const sql=q=>JSON.parse(execFileSync('psql',['postgres://localhost/artline?sslmode=disable','-XAt','-v','ON_ERROR_STOP=1','-c',q],{encoding:'utf8'}));
const audit=sql(`SELECT row_to_json(t) FROM (SELECT before_json,after_json FROM audit_log WHERE entity_type='artwork' AND entity_id='${id}' AND action='update' ORDER BY created_at DESC LIMIT 1)t`);
for(const key of Object.keys(audit.before_json))if(!['creation_year_start','creation_year_end','date_precision','revision','updated_at','updated_by'].includes(key))assert.deepEqual(audit.after_json[key],audit.before_json[key],`preserved ${key}`);
assert.equal(audit.before_json.creation_year_start,null);assert.equal(audit.after_json.creation_year_start,1882);assert.equal(audit.after_json.creation_year_end,1882);assert.equal(audit.after_json.date_precision,'exact');
assert.equal(sql(`SELECT to_json(count(*)) FROM citations WHERE entity_id='${id}' AND source_record_id='nationalmuseum-date-review:19182:20260911' AND field_name='creation_date'`),1);
const token=fs.readFileSync('apps/server/.env','utf8').match(/^ARTLINE_EDITOR_TOKEN=(.*)$/m)[1].trim().replace(/^(['"])(.*)\1$/,'$2');
const route=`http://localhost:8080/api/v1/museums/nationalmuseum-stockholm/works/${id}`;
const res=await fetch(route+'?preview=1',{headers:{Authorization:'Bearer '+token}});assert.equal(res.status,200);
const detail=await res.json();assert.equal(detail.creation_year_start,1882);assert.equal(detail.creation_year_end,1882);assert.equal(detail.date_precision,'exact');assert.equal(detail.date_display,'Signed 1882');assert.equal(detail.status,'review');assert.equal(detail.media_url,null);
assert(detail.citations.some(c=>c.source_url===receipt.source_url));
for(const [suffix,status]of [['',404],['?preview=1',401]])assert.equal((await fetch(route+suffix)).status,status);
fs.writeFileSync(output,JSON.stringify({passed:true,checked_at:new Date().toISOString(),unchanged_other_artworks:after.works.length-1,date_updated:1882,citation_count:1,api_checks:3,new_images:0,new_artworks:0},null,2),{flag:'wx'});
console.log('Date, source citation, audit trail, catalogue preservation and 3 API access checks passed.');
