// Read-only local verification. Usage: output.json receipt.json selection.json [...]
import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';

const [output, ...pairs] = process.argv.slice(2);
assert(output && pairs.length > 0 && pairs.length % 2 === 0, 'output receipt selection [...]');
assert(!fs.existsSync(output), 'never overwrite an existing verification receipt');
const require = createRequire(new URL('../apps/web/package.json', import.meta.url));
const sharp = require('sharp');
const token = fs.readFileSync('apps/server/.env', 'utf8').match(/^ARTLINE_EDITOR_TOKEN=(.*)$/m)[1].trim().replace(/^(['"])(.*)\1$/, '$2');
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const targets = [];
for (let i = 0; i < pairs.length; i += 2) {
  const receipt = JSON.parse(fs.readFileSync(pairs[i]));
  const raw = fs.readFileSync(pairs[i + 1]);
  assert.equal(receipt.Version, 'painter-coverage-images-100kb-v1');
  assert(receipt.Applied);
  assert.equal(receipt.SelectionSHA, hash(raw));
  const selection = JSON.parse(raw);
  for (const r of receipt.Results.filter(r => r.ImageOutcome === 'attached')) {
    const entry = selection.Entries.find(e => e.Candidate.ID === r.ArtworkID);
    assert(entry);
    targets.push({r, entry});
  }
}
assert.equal(new Set(targets.map(({r}) => r.ArtworkID)).size, targets.length);
assert(targets.length > 0 && targets.length <= 50);
const requests = [];
async function get(path, auth = true, expected = 200) {
  const start = performance.now();
  const response = await fetch('http://localhost:8080/api/v1/' + path, {
    headers: auth ? {Authorization: 'Bearer ' + token} : {}, signal: AbortSignal.timeout(20000),
  });
  requests.push({path, status: response.status, ms: Math.round(performance.now() - start)});
  assert.equal(response.status, expected, path);
  return response.json();
}
const museums = new Set();
const files = [];
for (const {r, entry} of targets) {
  const source = entry.Pick.Source;
  const museum = {
	'icons-athens-commons':'byzantine-christian-museum-athens',
	'popular-karlsruhe':'staatliche-kunsthalle-karlsruhe',
	'popular-karlsruhe-next':'staatliche-kunsthalle-karlsruhe',
    'popular-poldi':'museo-poldi-pezzoli',
    'popular-nivaagaard':'nivaagaards-malerisamling',
    'pinakothek-alte':'alte-pinakothek','pinakothek-neue':'neue-pinakothek',
    'pinakothek-durer-alte':'alte-pinakothek','pinakothek-durer-gnm':'germanisches-nationalmuseum',
    'pinakothek-durer-augsburg':'staatsgalerie-katharinenkirche-augsburg',
    chicago:'art-institute-of-chicago',nga:'national-gallery-of-art',cleveland:'cleveland-museum-of-art',
    smk:'statens-museum-for-kunst',met:'the-met','commons-met':'the-met','commons-met-highlight':'the-met',
  }[source];
  assert(museum, 'unreviewed source-to-museum mapping');
  museums.add(museum);
  const route = `museums/${museum}/works/${r.ArtworkID}`;
  const d = await get(route + '?preview=1');
  assert.equal(d.title, r.Title);
  assert.equal(d.status, 'review');
  assert.equal(d.media_url, r.Path);
  assert.equal(d.rights_status, entry.Rights);
  assert.equal(d.license_label, entry.License);
  assert.equal(d.license_url, entry.LicenseURL);
  assert.equal(d.source_page_url, entry.ImagePage);
  assert.equal(d.display, null);
  assert.equal(d.accession_number, entry.Accession);
	if(source === 'icons-athens-commons') {
		assert.equal(d.unlinked_creator_label, 'Workshops of Constantinople');
		assert.equal(d.object_form, 'icon');
		assert(d.attribution_text.includes('Yair-haklai'));
		assert(d.attribution_text.includes('CC BY-SA 4.0'));
	}
  if (r.Object === 'commons-met-highlight:488319') assert(d.selections.some(s => s.kind === 'museum'));
  await get(route, false, 404);
  await get(route + '?preview=1', false, 401);
  assert(r.Path.startsWith('/assets/artworks/imported/') && !r.Path.includes('..'));
  const file = fs.readFileSync('apps/web/public' + r.Path);
  assert(file.length <= 100000);
  assert.equal(file.length, r.Bytes);
  assert.equal(hash(file), r.Hash);
  const metadata = await sharp(file, {limitInputPixels: 1000000}).metadata();
  assert.equal(metadata.format, 'jpeg');
  assert.equal(metadata.width, r.Width);
  assert.equal(metadata.height, r.Height);
  assert(Math.max(metadata.width, metadata.height) <= 900);
  await sharp(file, {limitInputPixels: 1000000}).raw().toBuffer();
  const served = await fetch('http://localhost:3000' + r.Path, {signal: AbortSignal.timeout(20000)});
  assert.equal(served.status, 200);
  assert.equal(hash(Buffer.from(await served.arrayBuffer())), r.Hash);
  files.push({artwork: r.ArtworkID, artist: r.Artist, path: r.Path, bytes: file.length, sha256: r.Hash});
}
for (const museum of museums) {
  const route = `museums/${museum}/works?preview=1&image_only=1&limit=5`;
  const page = await get(route);
  assert.equal(page.items.length, Math.min(5, page.total));
  assert(page.total > 0);
  let nextItems = [];
  if (page.total > 5) {
    assert(page.next_cursor);
    const next = await get(route + '&cursor=' + encodeURIComponent(page.next_cursor));
    assert.equal(next.total, page.total);
    assert(next.items.length > 0 && next.items.length <= 5);
    assert(next.items.every(x => !page.items.some(y => y.id === x.id)));
    nextItems = next.items;
  } else assert(!page.next_cursor);
  for (const work of [...page.items, ...nextItems]) {
    assert(work.media_url);
    assert.equal(work.display, null);
  }
}
fs.writeFileSync(output, JSON.stringify({checked_at: new Date().toISOString(), passed: true, requests, files, decoded_images: files.length, served_hashes: files.length}, null, 2) + '\n', {flag: 'wx', mode: 0o600});
console.log(`${requests.length} API checks, ${files.length} full image decodes and served image hashes passed.`);
