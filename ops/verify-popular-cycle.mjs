// Read-only verification of a frozen all-popular cycle and its derived reports.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const [dir, receipt] = process.argv.slice(2);
assert(dir && receipt, 'usage: node ops/verify-popular-cycle.mjs cycle-directory receipt.json');
const read = p => JSON.parse(fs.readFileSync(path.join(dir,p)));
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const m = read('manifest.json'), summary = read('summary.json');
const inventory = fs.readFileSync(path.join(dir,'inventory/artworks.jsonl'));
assert.equal(sha(inventory),m.InventorySHA);
const works = inventory.toString().trim().split('\n').filter(Boolean).map(l=>JSON.parse(l));
const ids = new Set(works.map(w=>w.ID));
assert.equal(ids.size,works.length);
const expected = new Map(m.Artists.map(a=>[a.ID,[]]));
for(const w of works)for(const c of w.Credits)if(expected.has(c.ID))expected.get(c.ID).push(w.ID);
let checked=0, candidates=0, links=0;
for(const a of m.Artists){
 const r=read('painters/'+a.ID+'.json'), d=read('painters/'+a.ID+'.assessment.json');
 assert.equal(r.Fingerprint,m.Fingerprint);assert(r.AutomatedPassDone);assert.equal(r.ResearchComplete,false);
 assert.deepEqual(r.Works.map(w=>w.ID),expected.get(a.ID));
 assert.deepEqual(d.Works,r.Works);assert.equal(d.ResearchComplete,false);
 assert(fs.existsSync(path.join(dir,'painters',a.ID+'.md')));
 assert(fs.existsSync(path.join(dir,'inventory/painters',a.Slug+'.md')));
 if(r.Discovery.State==='bounded_catalogue_search_checked'){
  const bytes=fs.readFileSync(path.join(dir,r.Discovery.Capture));
  assert.equal(sha(bytes),r.Discovery.SHA);
  const raw=JSON.parse(bytes);assert.deepEqual(raw.data,r.Discovery.Candidates.map(c=>c.Raw));
  assert.deepEqual(raw.data,d.Discovery.Candidates.map(c=>c.Raw));
  assert(raw.data.length<=20);checked++;candidates+=raw.data.length;
 }
 links+=r.Works.length;
}
assert.equal(summary.painters_processed,m.Artists.length);assert.equal(summary.painters_research_complete,0);
assert.equal(summary.works,links);
const result={passed:true,painters:m.Artists.length,distinct_artworks:works.length,artwork_links:links,source_captures_verified:checked,discovery_results:candidates,inventory_sha256:m.InventorySHA,checked_at:new Date().toISOString()};
fs.mkdirSync(path.dirname(receipt),{recursive:true});
fs.writeFileSync(receipt,JSON.stringify(result,null,2)+'\n',{flag:'wx',mode:0o600});
console.log(result);

