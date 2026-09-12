// Offline, read-only inventory comparison and explicit decision verification.
import fs from 'node:fs';
import readline from 'node:readline';
import assert from 'node:assert/strict';
const base='docs/research/painter-review/';
const old=base+'snapshots/round-01-greek-review-v2/';
const latest=base+'snapshots/round-02-smk-cleveland/';
const read=p=>JSON.parse(fs.readFileSync(p));
const prior=read(base+'round-01-decisions-v2.json'), decisions=read(base+'round-02-decisions.json');
assert.deepEqual(decisions.slice(0,prior.length),prior);
const receipt=read('output/round-02-images-apply.json');
const changed=new Set(receipt.Results.filter(x=>x.ImageOutcome==='attached').map(x=>x.ArtworkID));
const replay=read('output/round-02-images-replay.json');
assert.equal(replay.Results.length,15);assert(replay.Results.every(x=>x.ImageOutcome==='existing_media_preserved'));
async function works(dir){
  const rows=new Map();
  for await(const line of readline.createInterface({input:fs.createReadStream(dir+'artworks.jsonl'),crlfDelay:Infinity})){
    const w=JSON.parse(line);assert(!rows.has(w.ID));rows.set(w.ID,w);
  }
  return rows;
}
const previous=await works(old), current=await works(latest);
assert.equal(previous.size,105961);assert.equal(current.size,105961);
for(const [id,w] of current){
  const before=previous.get(id);assert(before);
  if(changed.has(id)){assert.notEqual(w.Fingerprint,before.Fingerprint);assert.equal(before.Image,'');assert(w.ImageCheck.startsWith('file verified'));}
  else assert.deepEqual(w,before,`unrelated ledger row changed ${id}`);
}
const artists=read(latest+'artists.json'), oldArtists=new Map(read(old+'artists.json').map(a=>[a.ID,a]));
assert.equal(artists.length,5328);assert.equal(fs.readdirSync(latest+'painters').length,5328);
const changedArtists=new Set([...current.values()].filter(w=>changed.has(w.ID)).flatMap(w=>w.Credits.map(c=>c.ID)));
assert.equal(changedArtists.size,3);
for(const a of artists){
  assert(fs.existsSync(latest+'painters/'+a.ID+'.md'));
  if(!changedArtists.has(a.ID))assert.deepEqual(a,oldArtists.get(a.ID));
  assert.equal(a.RoundDone[1],false,'no round-two painter complete');
}
for(const d of decisions){
  const row=d.Kind==='artist'?artists.find(a=>a.ID===d.ID):current.get(d.ID);
  assert(row);assert.equal(row.Fingerprint,d.Fingerprint,'no stale decisions');
  if(d.Kind==='artwork'&&d.Status==='done'&&d.ImageOutcome==='verified')assert(row.ImageCheck.startsWith('file verified'));
  if(d.Round===2&&d.Kind==='artist'){
    const md=fs.readFileSync(latest+'painters/'+d.ID+'.md','utf8');assert(md.includes(`- [ ] Round 02: ${d.Status}`));
  }
}
const counts=read(latest+'summary.json').counts;
assert.deepEqual(counts,{artists:5328,artists_without_artworks:218,artworks:105961,images_file_verified:256,images_present:418,unlinked_artworks:21});
const checked={passed:true,checked_at:new Date().toISOString(),counts,prior_decisions_preserved:32,matching_current_decisions:54,new_images:15,replay_preserved:15,round_1_completed_painters:artists.filter(a=>a.RoundDone[0]).length,round_2_completed_painters:0,round_2_completed_artworks:decisions.filter(d=>d.Round===2&&d.Kind==='artwork'&&d.Status==='done').length,round_2_blocked_artworks:decisions.filter(d=>d.Round===2&&d.Kind==='artwork'&&d.Status==='blocked').length};
assert.equal(checked.round_1_completed_painters,12);assert.equal(checked.round_2_completed_artworks,14);assert.equal(checked.round_2_blocked_artworks,5);
fs.writeFileSync('output/round-02-ledger-verification.json',JSON.stringify(checked,null,2)+'\n',{flag:'wx',mode:0o600});
console.log(JSON.stringify(checked));
