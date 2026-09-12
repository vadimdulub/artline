import {readFile} from "node:fs/promises";
import {createHash} from "node:crypto";
import {createRequire} from "node:module";
import assert from "node:assert/strict";

const root=new URL("../",import.meta.url);
const require=createRequire(new URL("apps/web/package.json",root));
const sharp=require("sharp");
const selectionBytes=await readFile(new URL("docs/research/europe-ui-20260910/smk-images-v1.json",root));
const hash=b=>createHash("sha256").update(b).digest("hex");
assert.equal(hash(selectionBytes),"17a6c25903f8eeacd06f57e88c2ffdd1572e14f85358619af9ee2ca5c1207f23");
const selection=JSON.parse(selectionBytes);
const receipt=JSON.parse(await readFile(new URL("output/europe-smk-images-20260910-apply.json",root)));
assert.equal(receipt.Added,80);assert.equal(receipt.Failed,0);assert.equal(receipt.Results.length,80);
let total=0,max=0;const seen=new Set();
for(const result of receipt.Results){
  assert.equal(result.Outcome,"attached");
  assert.match(result.Path,/^\/assets\/artworks\/imported\/smk-[a-f0-9]{64}\.jpg$/);
  assert(!seen.has(result.Path));seen.add(result.Path);
  const item=selection.Images.find(image=>image.Object===result.Object);
  assert(item&&item.Raw.public_domain===true&&item.Raw.rights==="https://creativecommons.org/publicdomain/mark/1.0/");
  const bytes=await readFile(new URL("apps/web/public"+result.Path,root));
  assert(bytes.length>0&&bytes.length<=100000);assert.equal(bytes.length,result.Bytes);assert.equal(hash(bytes),result.Hash);
  const info=await sharp(bytes,{limitInputPixels:1000000}).metadata();
  assert.equal(info.format,"jpeg");assert.equal(info.width,result.Width);assert.equal(info.height,result.Height);
  assert(info.width<=700&&info.height<=700);
  total+=bytes.length;max=Math.max(max,bytes.length);
}
console.log(`Verified ${seen.size} local European artwork images: ${total} bytes total, largest ${max} bytes. All hashes, dimensions and rights-selection links match.`);
