// Explicit decisions for the eight source/object pairs reviewed on September 11.
// Not a generic automatic-completion rule. Preserve the earlier decisions intact.
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const pin = '415a0504ab5f7fd3ca4683687943e7f75e48c7e60088c137bb853b03ddc2f900';
const raw = fs.readFileSync('docs/research/painter-review/greek-round-01-selection-v2.json');
assert.equal(hash(raw),pin);
const manifest = JSON.parse(raw), receipt = JSON.parse(fs.readFileSync('output/greek-painter-review-batch2-apply-v1.json'));
assert(receipt.Applied && receipt.SHA===pin && receipt.Results.length===12);
for (const r of receipt.Results) assert(/^[a-f0-9-]{36}$/.test(r.ID));
const results = receipt.Results.filter(r=>r.Kind==='artwork');
const sql = q => execFileSync('psql',['postgres://localhost/artline?sslmode=disable','-XAt','-v','ON_ERROR_STOP=1','-c',q],{encoding:'utf8',maxBuffer:8*1024*1024});
let query = fs.readFileSync('apps/server/cmd/review-painters/ledger.go','utf8').match(/const ledgerWorksSQL = `([\s\S]*?)`/)[1];
query = query.replace('ORDER BY coalesce(aa.artist_id',`WHERE a.id IN (${results.map(r=>"'"+r.ID+"'").join(',')}) ORDER BY coalesce(aa.artist_id`);
const works = sql(query).trim().split('\n').map(line=>JSON.parse(line.slice(line.indexOf('|')+1)));
assert.equal(works.length,8);
const artists = JSON.parse(sql(`SELECT json_agg(t) FROM (SELECT a.id,md5(to_jsonb(a)::text||coalesce((SELECT string_agg(to_jsonb(ac)::text,'' ORDER BY ac.country_code,ac.relationship_type) FROM artist_countries ac WHERE ac.artist_id=a.id),'')) AS fingerprint,(SELECT count(*) FROM artwork_artists WHERE artist_id=a.id) AS works FROM artists a WHERE a.id IN (${receipt.Results.filter(r=>r.Kind==='artist').map(r=>"'"+r.ID+"'").join(',')})) t`));
const decisions = JSON.parse(fs.readFileSync('docs/research/painter-review/round-01-decisions.json'));
assert.equal(decisions.length,20);
const checked = new Date().toISOString();
for (const a of manifest.Artists) {
  const ar = receipt.Results.find(r=>r.Kind==='artist'&&r.Key===a.Key), dbArtist=artists.find(x=>x.id===ar.ID);
  const selected = manifest.Works.filter(w=>w.Artist===a.Key);
  assert.equal(selected.length,2); assert.equal(dbArtist.works,selected.length,'unreviewed database works added');
  const reviewed = [];
  for (const s of selected) {
    const wr=results.find(r=>r.Key===s.Key), w=works.find(x=>x.ID===wr.ID);
    assert.deepEqual(w.Credits,[{ID:ar.ID,Role:'primary'}]);
    for (const f of ['Title','Date','Accession']) assert.equal(w[f],s[f]);
    assert.equal(w.Source,s.URL); assert.equal(w.Scope,'eligible'); assert.equal(w.Image,''); reviewed.push(w);
    decisions.push({Kind:'artwork',ID:w.ID,Fingerprint:w.Fingerprint,Status:'done',ImageOutcome:'unavailable',Round:1,CheckedAt:checked,Sources:[s.URL,manifest.Policy.URL],
      Note:'Individually checked the museum object page, exact artist link, accession, literal creation date/range, medium, dimensions and collection credit. Photograph availability and source terms reviewed; no sufficiently verified reusable exact-object file established in this bounded search. Images remain unavailable to the app, not absent from the museum site. Permission or a separately licensed reproduction is still an open image follow-up.'});
  }
  reviewed.sort((a,b)=>a.ID.localeCompare(b.ID));
  const blocked = a.Key==='laskaridou-sofia';
  const extra = blocked ? ['https://www.searchculture.gr/aggregator/persons/-1625244741?language=en','https://www.nationalgallery.gr/wp-content/uploads/2021/10/adyta_gr.pdf'] : a.Uncertain ? ['https://www.nationalgallery.gr/wp-content/uploads/2021/10/4centuries_en.pdf'] : [];
  decisions.push({Kind:'artist',ID:ar.ID,Fingerprint:hash(dbArtist.fingerprint+reviewed.map(w=>w.ID+':'+w.Fingerprint).join('')),Status:blocked?'blocked':'done',Round:1,CheckedAt:checked,Sources:[a.URL,...selected.map(w=>w.URL),...extra],
    Note:blocked ? 'Two current database works reviewed. Painter review remains blocked on the 1876/1882 birth-date conflict. Messolonghi Lagoon (Π.3943) was researched but not added because museum web/printed dates and materials conflict. Numeric birth year remains unset.' : 'Round 1 review completed for the current two-work database scope and this bounded artist-catalogue search. Both selected objects have individual factual and image-availability decisions. Other catalogue entries and the full oeuvre remain follow-ups; this is not exhaustive museum coverage. '+(a.Uncertain?'The museum exhibition text qualifies the 1873 birth year; approximate display and unset numeric birth year preserve the uncertainty.':'')});
}
assert.equal(decisions.length,32);
const output='docs/research/painter-review/round-01-decisions-v2.json';
fs.writeFileSync(output,JSON.stringify(decisions,null,2)+'\n',{flag:'wx',mode:0o600});
console.log('Retained 20 prior decisions; added 8 work reviews, 3 bounded painter reviews and 1 blocked painter review. No new image-file completion flags.');
