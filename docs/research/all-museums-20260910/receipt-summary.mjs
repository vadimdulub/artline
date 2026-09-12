// Read-only reconciliation of actual receipts; no extrapolated source counts.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
const here=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(here,'../../..');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const before=read(path.join(root,'output/campaign-initial-before-verification.json'));
const after=read(path.join(root,'output/campaign-chicago-applied-verification.json'));
const api=read(path.join(root,'output/campaign-final-api-verification.json'));
const registry=read(path.join(here,'museum-register-after.json'));
const result={checked_at:new Date().toISOString(),before:before.counts,after:after.counts,types:after.types,creation_scope:after.creation_scope,sources:[]};
for(const source of ['met','cleveland','lombardia','chicago']){
 const selection=path.join(here,source+(['met','cleveland'].includes(source)?'-v2':'-v1'));
 const manifest=read(path.join(selection,'manifest.json'));
 const expected=read(path.join(selection,'summary.json'));
 const row={source,chunks:manifest.chunks.length,selected:0,created:0,reused:0,enriched:0,types_created:{},replay_unchanged:true};
 for(const c of manifest.chunks){
  const applied=read(path.join(root,`output/campaign-${source}-applied-20260910`,c.file));
  const replay=read(path.join(root,`output/campaign-${source}-replay-20260910`,c.file));
  const chunk=read(path.join(selection,c.file));
  assert(applied.applied&&replay.applied);
  assert.equal(c.works,applied.works.length);
  assert.equal(applied.created_artworks+applied.reused_artworks,c.works);
  assert.equal(replay.created_artworks,0);assert.equal(replay.added_citations,0);
  row.selected+=c.works;row.created+=applied.created_artworks;row.reused+=applied.reused_artworks;row.enriched+=applied.enriched_existing_artworks;
  const types=new Map(chunk.works.map(w=>[w.url,w.work_type]));
  for(const w of applied.works.filter(w=>w.outcome==='created')){const t=types.get(w.source_url);assert(t);row.types_created[t]=(row.types_created[t]||0)+1;}
 }
 assert.equal(row.selected,expected.selected);result.sources.push(row);
}
result.created=result.sources.reduce((n,r)=>n+r.created,0);
result.reused=result.sources.reduce((n,r)=>n+r.reused,0);
assert.equal(after.counts.artworks-before.counts.artworks,result.created);
for(const key of ['artists','media','published','display'])assert.equal(before.counts[key],after.counts[key]);
for(const phase of ['initial','chicago']){
 const applied=read(path.join(root,`output/campaign-${phase}-applied-verification.json`));
 const replay=read(path.join(root,`output/campaign-${phase}-replay-verification.json`));
 assert.deepEqual(applied.fingerprints,replay.fingerprints);assert.equal(applied.invalid,0);
}
result.registry={rows:registry.total_register_rows,represented_institutions:registry.represented_institution_rows,overlapping_source_rows:true};
assert.equal(registry.represented_institution_rows,after.counts.institutions);
result.csv_validation=JSON.parse(execFileSync('ruby',['-rcsv','-rjson','-e',`
 rows=CSV.read(ARGV[0],headers:true,encoding:'UTF-8'); source=JSON.parse(File.read(ARGV[1]));
 abort 'row count mismatch' unless rows.length==source['rows'].length
 abort 'column count mismatch' unless rows.headers.length==13
 source['rows'].each_with_index do |r,i|
  rows.headers.each do |key|
   expected=r[key].nil? ? '' : r[key].to_s
   expected=expected.sub(/^[=+@-]/){|s| "'"+s}
   abort "CSV field mismatch #{i}:#{key}" unless rows[i][key]==expected
  end
 end
 puts JSON.generate({rows:rows.length,columns:rows.headers.length,all_cells_match:true})
`,path.join(here,'museum-register-after.csv'),path.join(here,'museum-register-after.json')],{encoding:'utf8'}));
result.api_requests=api.requests.length;
result.limitations='Metadata review records, not validated masterpieces. No new images or current-display claims. Register rows overlap; catalogue coverage is incomplete. No 10-million-row benchmark.';
fs.writeFileSync(path.join(root,'output/campaign-final-summary-20260910.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx',mode:0o600});
console.log(JSON.stringify(result,null,2));
