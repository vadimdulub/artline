// Local read-only database/disk verification; writes only an immutable receipt.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import assert from 'node:assert/strict';

const [mode, output, beforePath, receiptPath] = process.argv.slice(2);
assert(['before', 'after'].includes(mode) && output, 'before|after output [baseline receipt]');
const db = 'postgres://localhost/artline?sslmode=disable';
const sql = (q) => JSON.parse(execFileSync('psql', [db, '-XAt', '-v', 'ON_ERROR_STOP=1', '-c', q], { encoding: 'utf8', maxBuffer: 100 * 1024 * 1024 }));
const rows = (q) => sql(`SELECT coalesce(json_agg(t),'[]') FROM (${q}) t`);
const hash = (b) => crypto.createHash('sha256').update(b).digest('hex');
const state = {
  checked_at: new Date().toISOString(),
  works: rows(`SELECT a.id,a.primary_media_id, a.revision,md5((to_jsonb(a)-ARRAY['primary_media_id','revision','updated_at','updated_by'])::text) AS metadata_hash,md5(to_jsonb(a)::text) AS full_hash FROM artworks a ORDER BY a.id`),
  artists_hash: sql(`SELECT to_json(md5(string_agg(to_jsonb(a)::text,'' ORDER BY a.id))) FROM artists a`),
  attributions_hash: sql(`SELECT to_json(md5(string_agg(to_jsonb(a)::text,'' ORDER BY a.artwork_id,a.artist_id))) FROM artwork_artists a`),
  locations_hash: sql(`SELECT to_json(md5(string_agg(to_jsonb(a)::text,'' ORDER BY a.id))) FROM artwork_location_assertions a`),
  media: rows(`SELECT id,storage_path,checksum_sha256,byte_size,md5(to_jsonb(m)::text) AS hash FROM media_assets m ORDER BY id`),
  selections: rows(`SELECT ci.id,ci.artwork_id,c.curator_kind,md5(to_jsonb(ci)::text) AS hash FROM curated_collection_items ci JOIN curated_collections c ON c.id=ci.collection_id ORDER BY ci.id`),
};
if (mode === 'after') {
  const before = JSON.parse(fs.readFileSync(beforePath));
  const receipt = JSON.parse(fs.readFileSync(receiptPath));
  assert(receipt.Applied);
  assert.equal(state.works.length, before.works.length, 'no artwork creation/deletion');
  for (const field of ['artists_hash', 'attributions_hash', 'locations_hash']) assert.equal(state[field], before[field], field);
  const attached = new Set(receipt.Results.filter(r => r.ImageOutcome === 'attached').map(r => r.ArtworkID));
  const oldWorks = new Map(before.works.map(w => [w.id,w]));
  for (const w of state.works) {
    const old = oldWorks.get(w.id);
    assert.equal(w.metadata_hash, old.metadata_hash, `metadata preserved ${w.id}`);
    if (attached.has(w.id)) { assert.equal(old.primary_media_id,null); assert(w.primary_media_id); assert.equal(w.revision, old.revision+1); }
    else assert.equal(w.full_hash,old.full_hash, `non-target untouched ${w.id}`);
  }
  const media = new Map(state.media.map(m => [m.id,m]));
  for(const m of before.media) assert.equal(media.get(m.id)?.hash,m.hash, 'existing media preserved');
  assert.equal(state.media.length-before.media.length,attached.size);
  const selected = new Map(state.selections.map(s => [s.id,s]));
  for(const s of before.selections) assert.equal(selected.get(s.id)?.hash,s.hash, 'existing selection preserved');
  assert.equal(state.selections.length-before.selections.length,receipt.Results.filter(r=>r.HighlightAdded).length);
  assert(['museum-masterpieces-100kb-v1','painter-coverage-images-100kb-v1'].includes(receipt.Version),'supported receipt version');
  const evidence = rows(`SELECT m.id,e.source_record_id,e.source_image_url,e.policy_url,e.evidence_json FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE e.adapter_version='${receipt.Version}'`);
  const verified = [];
  for(const r of receipt.Results.filter(r=>r.ImageOutcome==='attached')) {
    const w=state.works.find(w=>w.id===r.ArtworkID),m=media.get(w.primary_media_id);
    assert(m.storage_path.startsWith('/assets/artworks/imported/'));
    const file=path.join(process.cwd(),'apps/web/public',m.storage_path);
    const bytes=fs.readFileSync(file);
    assert(bytes.length<=100000); assert.equal(bytes.length,m.byte_size); assert.equal(hash(bytes),m.checksum_sha256); assert.equal(hash(bytes),r.Hash);
    assert(evidence.some(e=>e.id===m.id&&e.evidence_json.derivative_sha256===r.Hash),'rights evidence');
    verified.push({artwork:r.ArtworkID,path:m.storage_path,bytes:bytes.length,sha256:r.Hash});
  }
  state.verification={passed:true,new_images:attached.size,new_highlights:state.selections.length-before.selections.length,verified};
  console.log(JSON.stringify({passed:true,new_images:attached.size,new_highlights:state.verification.new_highlights,files_verified:verified.length}));
}
fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(state,null,2)+'\n',{flag:'wx',mode:0o600});
