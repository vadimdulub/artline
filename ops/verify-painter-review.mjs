// Read-only inventory, database preservation, and local API checks.
import fs from 'node:fs';
import readline from 'node:readline';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
const root='docs/research/painter-review/snapshots/',before=root+'round-01-start/',after=root+'round-01-greek-review/';
const load=p=>JSON.parse(fs.readFileSync(p));
const receipt=load('output/greek-painter-review-apply-v1.json'),replay=load('output/greek-painter-review-replay-v1.json');
assert(receipt.Applied&&replay.Applied);assert(replay.Results.every(r=>r.Outcome==='existing_preserved'));
const old=new Map(),all=new Map(),counts=new Map();
async function scan(path,fn){for await(const line of readline.createInterface({input:fs.createReadStream(path)})){fn(JSON.parse(line))}}
await scan(before+'artworks.jsonl',w=>{assert(!old.has(w.ID));old.set(w.ID,w.Fingerprint)});
await scan(after+'artworks.jsonl',w=>{assert(!all.has(w.ID));all.set(w.ID,w);if(old.has(w.ID))assert.equal(w.Fingerprint,old.get(w.ID),'existing artwork/media/attribution preserved');for(const c of w.Credits)counts.set(c.ID,(counts.get(c.ID)||0)+1)});
assert.equal(old.size,105943);assert.equal(all.size,105953);for(const id of old.keys())assert(all.has(id));
const artists=load(after+'artists.json');assert.equal(artists.length,5324);
const index=fs.readFileSync(after+'PAINTERS.md','utf8');assert.equal(new Set([...index.matchAll(/painters\/([a-f0-9-]{36})\.md/g)].map(m=>m[1])).size,artists.length);
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
assert.equal(artistDone,9);
const unlinked=fs.readFileSync(after+'UNLINKED_ARTWORKS.md','utf8');const unlinkedIDs=[...unlinked.matchAll(/Artwork ID: `([a-f0-9-]{36})`/g)].map(m=>m[1]);assert.equal(unlinkedIDs.length,21);for(const id of unlinkedIDs)assert.equal(all.get(id).Credits.length,0);
const db='postgres://localhost/artline?sslmode=disable';const sql=q=>JSON.parse(execFileSync('psql',[db,'-XAt','-v','ON_ERROR_STOP=1','-c',q],{encoding:'utf8',maxBuffer:10*1024*1024}));
const newArtistIDs=receipt.Results.filter(r=>r.Kind==='artist'&&r.Outcome==='created').map(r=>r.ID);for(const id of newArtistIDs)assert(/^[a-f0-9-]{36}$/.test(id));assert.equal(newArtistIDs.length,9);
const prior=load('output/painter-images-state-after-v4.json');
assert.equal(sql(`SELECT to_json(md5(string_agg(to_jsonb(a)::text,'' ORDER BY a.id))) FROM artists a WHERE a.id NOT IN (${newArtistIDs.map(id=>"'"+id+"'").join(',')})`),prior.artists_hash,'all 5315 old artist rows unchanged');
const totals=sql(`SELECT json_build_object('artists',(SELECT count(*) FROM artists),'artworks',(SELECT count(*) FROM artworks),'media',(SELECT count(*) FROM media_assets),'highlights',(SELECT count(*) FROM curated_collection_items ci JOIN curated_collections c ON c.id=ci.collection_id WHERE c.curator_kind='museum'),'owner',(SELECT count(*) FROM curated_collection_items ci JOIN curated_collections c ON c.id=ci.collection_id WHERE c.curator_kind='owner'),'published',(SELECT count(*) FROM artworks WHERE status='published'))`);
assert.deepEqual(totals,{artists:5324,artworks:105953,media:403,highlights:569,owner:5,published:0});
const token=fs.readFileSync('apps/server/.env','utf8').match(/^ARTLINE_EDITOR_TOKEN=(.*)$/m)[1].trim().replace(/^(['"])(.*)\1$/,'$2');
const requests=[];
async function get(path,auth=true,status=200){const response=await fetch('http://localhost:8080/api/v1/'+path,{headers:auth?{Authorization:'Bearer '+token}:{},signal:AbortSignal.timeout(20000)});requests.push({path,status:response.status});assert.equal(response.status,status);return response.json()}
const route='museums/national-gallery-greece/works';const first=await get(route+'?preview=1&limit=5');assert.equal(first.total,10);assert.equal(first.items.length,5);assert(first.next_cursor);
const next=await get(route+'?preview=1&limit=5&cursor='+encodeURIComponent(first.next_cursor));assert.equal(next.total,10);assert.equal(new Set([...first.items,...next.items].map(w=>w.id)).size,10);
for(const r of receipt.Results.filter(r=>r.Kind==='artwork')){
 const d=await get(route+'/'+r.ID+'?preview=1'),w=all.get(r.ID);
 assert.equal(d.title,w.Title);assert.equal(d.date_display,w.Date);assert.equal(d.accession_number,w.Accession);assert.equal(d.status,'review');assert.equal(d.media_url,null);assert.equal(d.display,null);assert.equal(d.selections.length,0);assert(d.creation_year_end<=1970);
 assert(d.citations.some(c=>c.field_name==='image_rights_review'&&c.source_url==='https://www.nationalgallery.gr/oroi-chrisis/'));
 await get(route+'/'+r.ID,false,404);await get(route+'/'+r.ID+'?preview=1',false,401);
}
for(const key of ['parthenis-konstantinos','economou-michael']){
 const d=await get('artists/greek-'+key+'?preview=1');assert.equal(d.timeline_basis,'estimated');
 assert.equal(sql(`SELECT json_build_object('birth',birth_year) FROM artists WHERE slug='greek-${key}'`).birth,null,'uncertain birth year is not invented');
 assert(d.timeline_display.includes(key==='parthenis-konstantinos'?'1878/1879':'1884 in this museum record'));
 const works=await get('artists/greek-'+key+'/works?preview=1&limit=5');assert.equal(works.items.length,1);
}
const output='output/painter-review-verification-v1.json';fs.writeFileSync(output,JSON.stringify({passed:true,checked_at:new Date().toISOString(),totals,old_artworks_preserved:old.size,old_artist_rows_preserved:5315,markdown_painter_pages:artists.length,unlinked_artworks:unlinkedIDs.length,round_1_painters_done:artistDone,round_1_artworks_done:10,full_rounds_complete:0,requests},null,2)+'\n',{flag:'wx',mode:0o600});
console.log(`Verified ${artists.length} painter pages, ${all.size} artworks, unchanged prior catalogue rows, 10 additions and ${requests.length} API checks.`);
