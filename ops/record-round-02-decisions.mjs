// Explicit decisions for this reviewed cohort, not an automatic completion rule.
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const sql=q=>execFileSync('psql',['postgres://localhost/artline?sslmode=disable','-XAt','-v','ON_ERROR_STOP=1','-c',q],{encoding:'utf8',maxBuffer:8*1024*1024});
const artistIDs=['e1200c9b-8fdb-4e8d-8963-81ed02bd4983','ed8ab094-58e2-4b73-8fc6-e261cf8b0899','1e0af779-3de1-4811-adab-6e7dcaaabf29'];
const quoted=artistIDs.map(x=>"'"+x+"'").join(',');
const before=JSON.parse(fs.readFileSync('docs/research/painter-review/round-01-decisions-v2.json'));
assert.equal(before.length,32);
const selectionRaw=fs.readFileSync('docs/research/painter-review/round-02-image-selection.json');
assert.equal(hash(selectionRaw),'9b739312caf9d68238bdaa161f4a96144b4f019e28a29c72a7f60293fe6f637c');
const selection=JSON.parse(selectionRaw), receipt=JSON.parse(fs.readFileSync('output/round-02-images-apply.json'));
assert(receipt.Applied && receipt.SelectionSHA===hash(selectionRaw));
assert.equal(receipt.Results.length,15); assert(receipt.Results.every(r=>r.ImageOutcome==='attached'));
assert(JSON.parse(fs.readFileSync('output/round-02-images-after.json')).verification.passed);
assert(JSON.parse(fs.readFileSync('output/round-02-images-api.json')).passed);
let query=fs.readFileSync('apps/server/cmd/review-painters/ledger.go','utf8').match(/const ledgerWorksSQL = `([\s\S]*?)`/)[1];
query=query.replace('ORDER BY coalesce(aa.artist_id',`WHERE aa.artist_id IN (${quoted}) ORDER BY coalesce(aa.artist_id`);
const works=sql(query).trim().split('\n').map(line=>JSON.parse(line.slice(line.indexOf('|')+1)));
assert.equal(works.length,35);
const artists=JSON.parse(sql(`SELECT json_agg(t) FROM (SELECT a.id,md5(to_jsonb(a)::text||coalesce((SELECT string_agg(to_jsonb(ac)::text,'' ORDER BY ac.country_code,ac.relationship_type) FROM artist_countries ac WHERE ac.artist_id=a.id),'')) AS fingerprint FROM artists a WHERE a.id IN (${quoted})) t`));
const blocked={
  '3de19685-7085-4ddb-b0fa-2d36cc4c5cbe':'KMS3192: fresh SMK notes derive the lower date bound from artist years and upper bound from museum accession. This is not an established creation range. Existing image retained; date-basis review remains open. The importer now defers this wording, without rewriting this existing record.',
  '4817bd7e-c5e9-494d-8064-2fd70762e0d4':'KMS8604: SMK creator authority 238_person conflicts with an inscription reading Prossalendi 1868. An inscription alone does not establish a replacement creator. Attribution reconciliation is required before image attachment or completion.',
  '33a10892-e506-41b3-bfeb-8e7abcbc5ef8':'KMS9034: source note puts 1868 in parentheses, while the existing catalogue stores a year. Meaning of source notation remains unresolved; do not silently remove uncertainty. Exact-object permitted image attached, but metadata review remains blocked.',
  '2c758667-6212-4128-bb17-52f568c9a505':'KMS9035: source note puts 1871 in parentheses, while the existing catalogue stores a year. Meaning of source notation remains unresolved. Exact-object permitted image attached, but metadata review remains blocked.',
  '4ceb4ed7-f4f8-4076-a1ca-228a930586b3':'Sunlight in the Blue Room: museum-contributed record corroborates title, creator, 1891 date, medium and dimensions. Exact named Commons file has a public-domain statement, but the existing 1,957,721-byte local derivative has no stored rights-evidence row. Source-to-local-file provenance and a compliant derivative remain unresolved; existing media preserved.',
};
const priorImageID='43c8698f-5f56-41d2-89e9-6221810e92d8';
const reviewIDs=new Set([...receipt.Results.map(r=>r.ArtworkID),priorImageID,...Object.keys(blocked)]);
assert.equal(reviewIDs.size,19);
const decisions=[...before], checked=new Date().toISOString();
for(const w of works.filter(w=>reviewIDs.has(w.ID))){
  assert.equal(w.Credits.length,1); assert.equal(w.Credits[0].Role,'primary');
  const entry=selection.Entries.find(x=>x.Candidate.ID===w.ID);
  const source=w.ID==='4ceb4ed7-f4f8-4076-a1ca-228a930586b3'?'https://artsandculture.google.com/asset/sunlight-in-the-blue-room-anna-ancher/mwE3yo7ZLwPcHA?hl=en':w.Source;
  assert(source.startsWith('https://'));
  const sources=[source];
  if(entry) sources.push(entry.Policy);
  if(!blocked[w.ID]){
    assert.equal(w.Scope,'eligible');assert(w.Image && w.Bytes<=100000 && w.Evidence && w.License);
    const file=fs.readFileSync('apps/web/public'+w.Image);assert.equal(hash(file),w.Checksum);assert.equal(file.length,w.Bytes);
    if(entry){assert.equal(w.Title,entry.Candidate.Title);assert.equal(w.Accession,entry.Accession);assert.equal(w.Source,entry.Page);}
    else {assert.equal(w.Accession,'KMS1093');sources.push('https://creativecommons.org/publicdomain/mark/1.0/');}
  }
  decisions.push({Kind:'artwork',ID:w.ID,Fingerprint:w.Fingerprint,Status:blocked[w.ID]?'blocked':'done',ImageOutcome:blocked[w.ID]?'':'verified',Round:2,CheckedAt:checked,Sources:sources,
    Note:blocked[w.ID] || 'Exact museum object, artist authority, title, accession and creation bounds reviewed against the fresh primary record; source medium, dimensions and credit retained in evidence. Museum holding is not current display. Local JPEG hash, size and rights evidence verified. No masterpiece designation inferred.'+(w.ID==='2a9800a3-9de9-4db0-9324-c01dde629082'?' Source note is approximately 1860 with 1858–1861 bounds; probable sitter identification is preserved.':'')});
}
for(const a of artists){
  const owned=works.filter(w=>w.Credits.some(c=>c.ID===a.id)).sort((a,b)=>a.ID.localeCompare(b.ID));
  const isGreco=a.id===artistIDs[2];
  decisions.push({Kind:'artist',ID:a.id,Fingerprint:hash(a.fingerprint+owned.map(w=>w.ID+':'+w.Fingerprint).join('')),Status:isGreco?'in_progress':'blocked',Round:2,CheckedAt:checked,
    Sources:isGreco?['https://clevelandart.org/art/1952.222','https://clevelandart.org/art/1926.247']:['https://www.smk.dk/list/kunstnerprofiler/',...owned.filter(w=>w.Source.startsWith('https://open.smk.dk/')).map(w=>w.Source)],
    Note:isGreco?'Only two of eighteen current works received a round-2 primary-source review. The other sixteen and further museum discovery remain pending. Greek-born artist coverage is not limited to holdings in Greece.':a.id===artistIDs[0]?'Eight current works considered: six completed and two blocked. Date-basis issue in KMS3192 and legacy Sunlight image provenance/size prevent completion. Further Skagens holdings remain discovery follow-up.':'Nine current works considered: six completed and three blocked. Queen Olga attribution and two parenthesized date notes remain unresolved. Museum profile snippets also disagree on birth year (1818/1819); raw object API and the published correspondence introduction support 1819, but no biography was overwritten. SMK Connect KMS8791 is an additional discovery lead, not yet imported.'});
}
assert.equal(decisions.length,54);
assert.equal(decisions.filter(x=>x.Round===2&&x.Kind==='artwork'&&x.Status==='done').length,14);
fs.writeFileSync('docs/research/painter-review/round-02-decisions.json',JSON.stringify(decisions,null,2)+'\n',{flag:'wx',mode:0o600});
console.log('Retained 32 prior decisions. Round 2: 14 completed artwork reviews, 5 blocked artworks, 2 blocked painters, 1 painter in progress. No completed full rounds.');
