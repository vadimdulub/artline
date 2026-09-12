import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';
const root=resolve(new URL('..',import.meta.url).pathname);
const after=JSON.parse(readFileSync(`${root}/output/normandy-after-verification.json`));
const token=readFileSync(`${root}/apps/server/.env`,'utf8').match(/^ARTLINE_EDITOR_TOKEN=(.*)$/m)[1].trim().replace(/^(['"])(.*)\1$/,'$2');
const requests=[];
async function get(route,authenticated=true,expected=200){
  const t=performance.now();
  const r=await fetch('http://localhost:8080/api/v1/'+route,{headers:authenticated?{Authorization:'Bearer '+token}:{},signal:AbortSignal.timeout(12000)});
  requests.push({route,status:r.status,ms:Math.round(performance.now()-t)});
  assert.equal(r.status,expected,route);return r.json();
}
for(const slug of ['muma-le-havre','musee-beaux-arts-rouen']){
  const expected=after.museums.find(m=>m.slug===slug).artworks;
  const museum=await get(`museums/${slug}?preview=1`);
  assert.equal(museum.work_count,expected);assert.equal(museum.on_view_count,0);
  const first=await get(`museums/${slug}/works?preview=1&limit=5`);
  assert.equal(first.items.length,5);assert.equal(first.total,expected);
  const next=await get(`museums/${slug}/works?preview=1&limit=5&cursor=${encodeURIComponent(first.next_cursor)}`);
  assert.equal(next.items.length,5);assert.ok(next.items.every(w=>!first.items.some(x=>x.id===w.id)));
  assert.ok(first.items.every(w=>!w.display&&!w.description_md));
  const detail=await get(`museums/${slug}/works/${first.items[0].id}?preview=1`);
  assert.ok(detail.description_md);
  const display=await get(`museums/${slug}/works?preview=1&display=on_view&limit=5`);assert.equal(display.total,0);
  const painters=await get(`museums/${slug}/works?preview=1&artist=claude-monet&artist=camille-pissarro-q134741&limit=5`);
  assert.ok(painters.items.length>0);assert.ok(painters.items.every(w=>w.artists.some(a=>['claude-monet','camille-pissarro-q134741'].includes(a.slug))));
  await get(`museums/${slug}?preview=1`,false,401);await get(`museums/${slug}`,false,404);
}
const highlights=await get('museums/muma-le-havre/works?preview=1&selection=museum&limit=5');
assert.equal(highlights.total,30);assert.ok(highlights.items.every(w=>w.selections.some(s=>s.kind==='museum'&&s.source_url==='https://www.muma-lehavre.fr/fr/collections/oeuvres-commentees/incontournable')));
for(const source of ['muma','rouen']){
  const receipt=JSON.parse(readFileSync(`${root}/output/normandy-${source}-apply-20260910/chunk-001.json`));
  const title=source==='muma'?'Les Nymphéas':'Démocrite';
  const work=receipt.works.find(w=>w.title===title);assert.ok(work);
  const detail=await get(`museums/${work.museum}/works/${work.artwork_id}?preview=1`);
  assert.equal(detail.title,title);assert.equal(detail.media_url,null);
  if(source==='muma')assert.ok(detail.description_md.includes('Dimensions require review'));
}
for(const artist of ['claude-monet','camille-pissarro-q134741']){
  const page=await get(`artists/${artist}/works?preview=1&limit=5`);assert.ok(page.items.length<=5);
}
writeFileSync(`${root}/output/normandy-api-verification.json`,JSON.stringify({checked_at:new Date().toISOString(),requests,limitation:'Single local HTTP checks, not browser tests or a production concurrency/scale benchmark.'},null,2)+'\n',{flag:'wx',mode:0o600});
const directory=JSON.parse(readFileSync(`${root}/docs/research/normandy-20260910/audit/museum-directory.json`));
const aliases={M0720:'muma-le-havre',M0729:'musee-beaux-arts-rouen'};
const coverage=directory.map(d=>{
  const m=after.museums.find(m=>m.slug===(aliases[d.code]||'joconde-'+d.code.toLowerCase()));
  return {...d,linked_institution:m?.slug||null,local_artworks:m?.artworks??null,local_images:m?.images??null,
    coverage_state:m?'partial_sourced_catalogue':'not_mapped_no_zero_coverage_claim'};
});
writeFileSync(`${root}/docs/research/normandy-20260910/museum-coverage.json`,JSON.stringify({checked_at:new Date().toISOString(),scope:'90 Muséofile Normandy entries; not every museum in Normandy or Europe. Painting candidate is thematic discovery only; source catalogue counts are not eligible-artwork totals.',rows:coverage},null,2)+'\n',{flag:'wx',mode:0o600});
console.log(`${requests.length} bounded API checks passed; 90-entry museum coverage report saved.`);
