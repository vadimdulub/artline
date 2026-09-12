import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
const require=createRequire(new URL('../apps/web/package.json',import.meta.url));
const sharp=require('sharp');
const token=fs.readFileSync('apps/server/.env','utf8').match(/^ARTLINE_EDITOR_TOKEN=(.*)$/m)[1].trim().replace(/^(['"])(.*)\1$/,'$2');
const receipt=JSON.parse(fs.readFileSync('output/masterpieces-apply-v1.json'));
const added=receipt.Results.filter(r=>r.ImageOutcome==='attached');
const requests=[];
async function get(path,auth=true,expected=200){
 const started=performance.now();const r=await fetch('http://localhost:8080/api/v1/'+path,{headers:auth?{Authorization:'Bearer '+token}:{},signal:AbortSignal.timeout(20000)});
 requests.push({path,status:r.status,ms:Math.round(performance.now()-started)});assert.equal(r.status,expected,path);return r.json();
}
for(const slug of ['the-met','cleveland-museum-of-art']){
 const m=await get(`museums/${slug}?preview=1`);assert(m.highlight_count>0);assert.equal(m.on_view_count,0);
 const page=await get(`museums/${slug}/works?preview=1&selection=museum&image_only=1&limit=5`);
 assert(page.items.length===5);assert(page.total>5);assert(page.next_cursor);
 for(const item of page.items){assert(item.media_url);assert(item.selections.some(s=>s.kind==='museum'&&s.source_url&&s.checked_at));assert.equal(item.display,null);}
 const next=await get(`museums/${slug}/works?preview=1&selection=museum&image_only=1&limit=5&cursor=${encodeURIComponent(page.next_cursor)}`);
 assert.equal(next.total,page.total);assert(next.items.every(x=>!page.items.some(y=>x.id===y.id)));
 await get(`museums/${slug}/works?preview=1`,false,401);
}
for(const object of ['met:435809','met:437869','met:435868','cleveland:122351']){
 const r=added.find(x=>x.Object===object);assert(r);const museum=object.startsWith('met:')?'the-met':'cleveland-museum-of-art';
 const d=await get(`museums/${museum}/works/${r.ArtworkID}?preview=1`);
 assert.equal(d.title,r.Title);assert.equal(d.status,'review');assert.equal(d.rights_status,'cc0');
 assert.equal(d.media_url,r.Path);assert.equal(d.license_label,'CC0 1.0');assert(d.selections.some(s=>s.kind==='museum'));
 assert.equal(d.display,null);
 const response=await fetch('http://localhost:3000'+r.Path,{signal:AbortSignal.timeout(12000)});assert.equal(response.status,200);
 const data=Buffer.from(await response.arrayBuffer());assert.equal(crypto.createHash('sha256').update(data).digest('hex'),r.Hash);
 await get(`museums/${museum}/works/${r.ArtworkID}`,false,404);
}
for(const r of added){const file=fs.readFileSync('apps/web/public'+r.Path);const m=await sharp(file,{limitInputPixels:1000000}).metadata();assert.equal(m.format,'jpeg');assert.equal(m.width,r.Width);assert.equal(m.height,r.Height);assert(file.length<=100000);}
fs.writeFileSync('output/masterpieces-api-verification-v1.json',JSON.stringify({checked_at:new Date().toISOString(),requests,decoded_images:added.length},null,2)+'\n',{flag:'wx',mode:0o600});
console.log(`${requests.length} API checks, four served image hashes and ${added.length} image decodes passed.`);
