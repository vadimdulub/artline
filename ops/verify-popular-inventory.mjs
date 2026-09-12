// Cross-check every popular artist/artwork Markdown entry against the local DB.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
const dir=process.argv[2]||'docs/research/popular-artists-20260911/inventory-v2';
const output=process.argv[3]||'output/popular-inventory-verification.json';
const sql=q=>JSON.parse(execFileSync('psql',['postgres://localhost/artline?sslmode=disable','-XAt','-v','ON_ERROR_STOP=1','-c',q],{encoding:'utf8',maxBuffer:30<<20}));
const summary=JSON.parse(fs.readFileSync(dir+'/summary.json'));
const works=fs.readFileSync(dir+'/artworks.jsonl','utf8').trim().split('\n').map(JSON.parse);
const artists=sql(`SELECT json_agg(t) FROM (SELECT a.id,a.slug,a.display_name,coalesce((SELECT json_agg(aa.artwork_id ORDER BY aa.artwork_id) FROM artwork_artists aa WHERE aa.artist_id=a.id),'[]') works FROM artists a JOIN artist_discovery_selection d ON d.artist_id=a.id WHERE d.is_popular ORDER BY a.id)t`);
assert.equal(artists.length,100);assert.equal(summary.artists,artists.length);
assert.equal(new Set(works.map(w=>w.ID)).size,works.length);assert.equal(works.length,summary.artworks);
assert.equal(works.length,new Set(artists.flatMap(a=>a.works)).size);
assert.equal(works.filter(w=>w.Image).length,summary.images_present);
assert.equal(works.filter(w=>w.NGAObject).length,summary.nga_image_feed_checked);
assert.equal(works.filter(w=>w.HoldingEvidence).length,summary.accepted_holding_evidence);
const index=fs.readFileSync(dir+'/PAINTERS.md','utf8');
const filenames=fs.readdirSync(dir+'/painters').filter(f=>f.endsWith('.md'));assert.equal(filenames.length,100);
let rows=0,localLinks=0;
for(const a of artists){
 const file=path.join(dir,'painters',a.slug+'.md');const md=fs.readFileSync(file,'utf8');
 assert(index.includes(`painters/${a.slug}.md`));assert(md.includes(a.id));
 const ids=[...md.matchAll(/<code>([a-f0-9-]{36})<\/code>/g)].map(m=>m[1]);
 assert.deepEqual(ids.sort(),a.works.sort(),a.display_name);rows+=ids.length;
 for(const w of works.filter(w=>a.works.includes(w.ID))){
  const line=md.split('\n').find(l=>l.includes(`<code>${w.ID}</code>`));
  assert(line.includes('Attribution: '+w.Credits.find(c=>c.ID===a.id).Role));
  assert(!line.includes('research complete'));
 }
 for(const m of md.matchAll(/\[local file\]\(<([^>]+)>\)/g)){assert(fs.existsSync(path.resolve(path.dirname(file),m[1])));localLinks++}
}
const imageChecks=works.reduce((a,w)=>(a[w.ImageCheck]=(a[w.ImageCheck]||0)+1,a),{});
const monet=artists.find(a=>a.slug==='claude-monet');assert.equal(monet.works.length,298);
const monetPictures=sql(`SELECT to_json(count(a.primary_media_id)) FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE aa.artist_id='${monet.id}'`);
assert.equal(works.filter(w=>monet.works.includes(w.ID)&&w.Image).length,monetPictures);
const findings=fs.readFileSync('docs/research/popular-artists-20260911/FINDINGS.md','utf8');
const deferred=JSON.parse(fs.readFileSync('docs/research/popular-artists-20260911/marmottan-v2/deferred.json'));
for(const d of deferred)assert(findings.includes(d.url),d.url);
const report={checked_at:new Date().toISOString(),passed:true,summary,markdown_rows:rows,local_links_checked:localLinks,image_checks:imageChecks,deferred_candidates:deferred.length};
fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n',{flag:'wx',mode:0o600});console.log(JSON.stringify(report,null,2));
