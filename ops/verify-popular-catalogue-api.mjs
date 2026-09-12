import fs from 'node:fs';
import assert from 'node:assert/strict';
const output=process.argv[2];assert(output&&!fs.existsSync(output));
const receipt=JSON.parse(fs.readFileSync(process.argv[3]||'output/popular-marmottan-apply-v2/chunk-001.json'));
const selection=JSON.parse(fs.readFileSync(process.argv[4]||'docs/research/popular-artists-20260911/marmottan-v2/chunk-001.json'));
assert(receipt.applied&&receipt.works.length>0&&receipt.works.length<=500&&receipt.works.length===selection.works.length);
const token=fs.readFileSync('apps/server/.env','utf8').match(/^ARTLINE_EDITOR_TOKEN=(.*)$/m)[1].trim().replace(/^(['"])(.*)\1$/,'$2');
const checks=[];
function museumFor(w) {
 const definition=selection.definitions?.[w.institution];
 assert(definition?.Slug && /^[a-z0-9-]+$/.test(definition.Slug), 'Missing pinned institution definition');
 return definition.Slug;
}
for(const r of receipt.works){
 const w=selection.works.find(x=>x.url===r.source_url);assert(w);
 const museum=museumFor(w);
 const route=`http://localhost:8080/api/v1/museums/${museum}/works/${r.artwork_id}`;
 const response=await fetch(route+'?preview=1',{headers:{Authorization:'Bearer '+token},signal:AbortSignal.timeout(20000)});
 assert.equal(response.status,200);const d=await response.json();
 assert.equal(d.id,r.artwork_id);assert.equal(d.title,w.title);assert.equal(d.accession_number,w.accession||null);assert.equal(d.status,'review');
 assert.equal(d.holding.slug,museum);assert.equal(d.display,null);
 assert(d.citations.some(c=>c.source_url===w.url));
 if(r.outcome==='created'){
  assert.equal(d.creation_year_start,w.creation_date.first);assert.equal(d.creation_year_end,w.creation_date.last);assert.equal(d.date_precision,w.creation_date.precision);
  assert.equal(d.medium_text,w.medium);assert.equal(d.dimensions_text,w.dimensions);assert.equal(d.selections.length,0);assert.equal(d.media_url,null);
 }
 checks.push({id:d.id,status:response.status,accession:d.accession_number});
}
const first=receipt.works[0].artwork_id;
const firstMuseum=museumFor(selection.works.find(x=>x.url===receipt.works[0].source_url));
for(const [suffix,status]of [['',404],['?preview=1',401]]){
 const r=await fetch(`http://localhost:8080/api/v1/museums/${firstMuseum}/works/${first}${suffix}`);assert.equal(r.status,status);
}
fs.writeFileSync(output,JSON.stringify({checked_at:new Date().toISOString(),passed:true,detail_checks:checks,auth_checks:2},null,2)+'\n',{flag:'wx',mode:0o600});
console.log(`${checks.length} object details and 2 access-control checks passed.`);
