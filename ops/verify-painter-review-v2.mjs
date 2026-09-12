// Read-only data/API verification of the second Greek cohort and full inventory.
import fs from 'node:fs';
import readline from 'node:readline';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
const root='docs/research/painter-review/', before=root+'snapshots/round-01-greek-review/', after=root+'snapshots/round-01-greek-review-v2/';
const load=p=>JSON.parse(fs.readFileSync(p));
const receipt=load('output/greek-painter-review-batch2-apply-v1.json'), replay=load('output/greek-painter-review-batch2-replay-v1.json'), preview=load('output/greek-painter-review-batch2-preview-v1.json');
const manifest=load(root+'greek-round-01-selection-v2.json');
assert(!preview.Applied&&preview.Results.length===12); assert(receipt.Applied&&replay.Applied);
assert.equal(receipt.SHA,'415a0504ab5f7fd3ca4683687943e7f75e48c7e60088c137bb853b03ddc2f900');
assert(replay.Results.every(r=>r.Outcome==='existing_preserved'));
assert(receipt.Results.every(r=>r.Outcome==='created'));
assert.deepEqual(replay.Results.map(r=>r.ID),receipt.Results.map(r=>r.ID));
const old=new Map(), all=new Map(), counts=new Map();
async function scan(path,fn){for await(const line of readline.createInterface({input:fs.createReadStream(path)}))fn(JSON.parse(line))}
await scan(before+'artworks.jsonl',w=>{assert(!old.has(w.ID));old.set(w.ID,w.Fingerprint)});
await scan(after+'artworks.jsonl',w=>{
  assert(!all.has(w.ID));all.set(w.ID,w);
  if(old.has(w.ID))assert.equal(w.Fingerprint,old.get(w.ID),'old work/media/attribution/source IDs changed');
  for(const c of w.Credits)counts.set(c.ID,(counts.get(c.ID)||0)+1);
});
assert.equal(old.size,105953);assert.equal(all.size,105961);for(const id of old.keys())assert(all.has(id));
const artists=load(after+'artists.json'), oldArtists=load(before+'artists.json');assert.equal(artists.length,5328);
const byArtist=new Map(artists.map(a=>[a.ID,a]));
for(const a of oldArtists)assert.equal(byArtist.get(a.ID)?.Fingerprint,a.Fingerprint,'old artist/country/linked-work fingerprint changed');
assert.equal(oldArtists.length,5324);
const index=fs.readFileSync(after+'PAINTERS.md','utf8');
assert.equal(new Set([...index.matchAll(/painters\/([a-f0-9-]{36})\.md/g)].map(m=>m[1])).size,artists.length);
let artistDone=0;
for(const a of artists){
  const page=fs.readFileSync(after+'painters/'+a.ID+'.md','utf8');
  const ids=[...page.matchAll(/Artwork ID: `([a-f0-9-]{36})`/g)].map(m=>m[1]);
  assert.equal(ids.length,counts.get(a.ID)||0);assert.equal(new Set(ids).size,ids.length);assert.equal(ids.length,a.Works);
  for(const id of ids)assert(all.get(id).Credits.some(c=>c.ID===a.ID));
  assert.equal([...page.matchAll(/^- \[[ x]\] Round \d\d:/gm)].length,10);
  if(page.includes('[x] Round 01: done'))artistDone++;
  assert(!/\[x\] Round (0[2-9]|10):/.test(page));
}
assert.equal(artistDone,12);
const unlinkedIDs=[...fs.readFileSync(after+'UNLINKED_ARTWORKS.md','utf8').matchAll(/Artwork ID: `([a-f0-9-]{36})`/g)].map(m=>m[1]);
assert.equal(unlinkedIDs.length,21);for(const id of unlinkedIDs)assert.equal(all.get(id).Credits.length,0);
const decisions=load(root+'round-01-decisions-v2.json');
assert.deepEqual(decisions.slice(0,20),load(root+'round-01-decisions.json'));
assert.equal(decisions.filter(d=>d.Kind==='artwork'&&d.Status==='done').length,18);
for(const r of receipt.Results.filter(r=>r.Kind==='artwork')){assert.equal(all.get(r.ID).Image,'');assert.equal(all.get(r.ID).ImageCheck,'missing');}
const sql=q=>JSON.parse(execFileSync('psql',['postgres://localhost/artline?sslmode=disable','-XAt','-v','ON_ERROR_STOP=1','-c',q],{encoding:'utf8',maxBuffer:8*1024*1024}));
const totals=sql(`SELECT json_build_object('artists',(SELECT count(*) FROM artists),'artworks',(SELECT count(*) FROM artworks),'media',(SELECT count(*) FROM media_assets),'highlights',(SELECT count(*) FROM curated_collection_items ci JOIN curated_collections c ON c.id=ci.collection_id WHERE c.curator_kind='museum'),'owner',(SELECT count(*) FROM curated_collection_items ci JOIN curated_collections c ON c.id=ci.collection_id WHERE c.curator_kind='owner'),'published',(SELECT count(*) FROM artworks WHERE status='published'))`);
assert.deepEqual(totals,{artists:5328,artworks:105961,media:403,highlights:569,owner:5,published:0});
assert.equal(sql(`SELECT to_json(count(*)) FROM external_identifiers WHERE scheme='nationalgallery-gr-work' AND external_id='messolonghi-lagoon-7672'`),0);
const token=fs.readFileSync('apps/server/.env','utf8').match(/^ARTLINE_EDITOR_TOKEN=(.*)$/m)[1].trim().replace(/^(['"])(.*)\1$/,'$2');
const requests=[];
async function get(path,auth=true,status=200){
  const r=await fetch('http://localhost:8080/api/v1/'+path,{headers:auth?{Authorization:'Bearer '+token}:{},signal:AbortSignal.timeout(20000)});
  requests.push({path,status:r.status});assert.equal(r.status,status,path);return r.json();
}
const route='museums/national-gallery-greece/works', museumIDs=new Set();let cursor='';
for(let page=0;page<4;page++){
  const d=await get(route+'?preview=1&limit=5'+(cursor?'&cursor='+encodeURIComponent(cursor):''));
  assert.equal(d.total,18);assert(d.items.length<=5);
  for(const w of d.items){assert(!museumIDs.has(w.id));museumIDs.add(w.id)}
  cursor=d.next_cursor;if(!cursor)break;
}
assert.equal(museumIDs.size,18);assert(!cursor);
for(const s of manifest.Works){
  const r=receipt.Results.find(r=>r.Kind==='artwork'&&r.Key===s.Key), d=await get(route+'/'+r.ID+'?preview=1');
  assert(museumIDs.has(r.ID));
  for(const [key,value] of Object.entries({title:s.Title,date_display:s.Date,accession_number:s.Accession,medium_text:s.Medium,dimensions_text:s.Dimensions,date_precision:s.Precision,creation_year_start:s.Year,creation_year_end:s.LastYear,status:'review',media_url:null,display:null}))assert.equal(d[key],value,key+': '+s.Key);
  assert.equal(d.selections.length,0);assert(d.creation_year_end<=1970);
  assert(d.citations.some(c=>c.field_name==='image_rights_review'&&c.source_url===manifest.Policy.URL));
  assert(d.citations.some(c=>c.field_name==='catalogue_metadata'&&c.source_url===s.URL));
  await get(route+'/'+r.ID,false,404);await get(route+'/'+r.ID+'?preview=1',false,401);
}
for(const a of manifest.Artists){
  const slug='greek-'+a.Key, d=await get('artists/'+slug+'?preview=1');
  assert.equal(d.timeline_basis,a.Uncertain?'estimated':'life');
  const life=sql(`SELECT json_build_object('birth',birth_year,'death',death_year,'bio',biography_md) FROM artists WHERE slug='${slug}'`);
  assert.equal(life.birth,a.Uncertain?null:a.Start);assert.equal(life.death,a.End);assert.equal(life.bio,a.Biography);
  const first=await get('artists/'+slug+'/works?preview=1&limit=1');assert.equal(first.items.length,1);assert(first.next_cursor);
  const next=await get('artists/'+slug+'/works?preview=1&limit=1&cursor='+encodeURIComponent(first.next_cursor));
  assert.equal(next.items.length,1);assert.notEqual(first.items[0].id,next.items[0].id);assert(!next.next_cursor);
}
fs.writeFileSync('output/painter-review-verification-v2.json',JSON.stringify({passed:true,checked_at:new Date().toISOString(),totals,old_artworks_preserved:old.size,old_painters_preserved:oldArtists.length,markdown_painter_pages:artists.length,unlinked_artworks:unlinkedIDs.length,round_1_painters_done:artistDone,round_1_artworks_done:18,full_rounds_complete:0,new_images:0,requests},null,2)+'\n',{flag:'wx',mode:0o600});
console.log(`Verified ${artists.length} painter pages, ${all.size} works, all prior fingerprints, 12 new records and ${requests.length} API checks.`);
