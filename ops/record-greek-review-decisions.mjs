// Record only the ten individually reviewed source/object pairs from the pinned
// first Greek batch. This is not an automatic completion rule for future imports.
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const db = 'postgres://localhost/artline?sslmode=disable';
const pin = 'b91b869d01d13e8889182b77f99b2867298cc0ca22637b3b253a0966b56eadc0';
const raw = fs.readFileSync('docs/research/painter-review/greek-round-01-selection.json');assert.equal(hash(raw),pin);
const manifest=JSON.parse(raw),receipt=JSON.parse(fs.readFileSync('output/greek-painter-review-apply-v1.json'));
assert(receipt.Applied && receipt.SHA===pin && receipt.Results.length===20);
const results=receipt.Results.filter(r=>r.Kind==='artwork');
for(const r of receipt.Results)assert(/^[a-f0-9-]{36}$/.test(r.ID));
const sql=q=>execFileSync('psql',[db,'-XAt','-v','ON_ERROR_STOP=1','-c',q],{encoding:'utf8',maxBuffer:8*1024*1024});
// Use the exporter's exact canonical fingerprint definition, restricted to this
// ten-work receipt. It cannot accidentally complete unrelated catalogue records.
let query=fs.readFileSync('apps/server/cmd/review-painters/ledger.go','utf8').match(/const ledgerWorksSQL = `([\s\S]*?)`/)[1];
query=query.replace('ORDER BY coalesce(aa.artist_id',`WHERE a.id IN (${results.map(r=>"'"+r.ID+"'").join(',')}) ORDER BY coalesce(aa.artist_id`);
const works=sql(query).trim().split('\n').map(line=>JSON.parse(line.slice(line.indexOf('|')+1)));
assert.equal(works.length,10);
const artists=JSON.parse(sql(`SELECT json_agg(t) FROM (SELECT a.id,md5(to_jsonb(a)::text||coalesce((SELECT string_agg(to_jsonb(ac)::text,'' ORDER BY ac.country_code,ac.relationship_type) FROM artist_countries ac WHERE ac.artist_id=a.id),'')) AS fingerprint,(SELECT count(*) FROM artwork_artists WHERE artist_id=a.id) AS works FROM artists a WHERE a.id IN (${receipt.Results.filter(r=>r.Kind==='artist').map(r=>"'"+r.ID+"'").join(',')})) t`));
const decisions=[],checked=new Date().toISOString();
for(const a of manifest.Artists){
 const ar=receipt.Results.find(r=>r.Kind==='artist'&&r.Key===a.Key),dbArtist=artists.find(x=>x.id===ar.ID);
 const selected=manifest.Works.find(w=>w.Artist===a.Key),wr=receipt.Results.find(r=>r.Kind==='artwork'&&r.Key===selected.Key),w=works.find(x=>x.ID===wr.ID);
 assert.equal(dbArtist.works,1,'new catalogue additions require another review');
 assert.deepEqual(w.Credits,[{ID:ar.ID,Role:'primary'}]);
 assert.equal(w.Title,selected.Title);assert.equal(w.Date,selected.Date);assert.equal(w.Accession,selected.Accession);assert.equal(w.Source,selected.URL);assert.equal(w.Image,'');
 decisions.push({Kind:'artwork',ID:w.ID,Fingerprint:w.Fingerprint,Status:'done',ImageOutcome:'unavailable',Round:1,CheckedAt:checked,Sources:[selected.URL,manifest.Policy.URL],Note:'Individually checked the title, literal creation date, accession, named artist link, medium, dimensions and collection credit. Image availability reviewed: the museum photograph is visible, but unrestricted republication permission is not established. No download; permission or a separately licensed exact reproduction remains an image follow-up.'});
 decisions.push({Kind:'artist',ID:ar.ID,Fingerprint:hash(dbArtist.fingerprint+w.ID+':'+w.Fingerprint),Status:a.Key==='economou-michael'?'blocked':'done',Round:1,CheckedAt:checked,Sources:[a.URL,selected.URL],Note:a.Key==='economou-michael'?'Birth-date discrepancy (1884 in the museum record versus 1888 elsewhere) remains unresolved; numeric birth year intentionally unset. The selected work has its own completed factual/image-availability review.':'Round 1 source review finished for the current one-work database scope: exact museum artist identity and dates checked, artist catalogue inspected for additions, selected work added and reviewed. This is not a complete oeuvre or a claim that the museum catalogue was exhausted. '+(a.Uncertain?'The source’s uncertain 1878/1879 birth date is preserved without an invented exact year.':'')});
}
const output='docs/research/painter-review/round-01-decisions.json';fs.writeFileSync(output,JSON.stringify(decisions,null,2)+'\n',{flag:'wx',mode:0o600});console.log('Recorded 10 artwork reviews, 9 bounded painter reviews and 1 unresolved painter review; rounds 2–10 untouched.');
