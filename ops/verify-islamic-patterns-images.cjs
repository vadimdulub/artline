// Rebuild the guide's responsive images from its original, user-supplied HTML.
// Run from the repo root: node ops/verify-islamic-patterns-images.cjs <input.html>
// This verifies against the committed receipts; it never replaces catalogue IDs.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { createRequire } = require('node:module');
const web = path.resolve(__dirname, '../apps/web');
const requireWeb = createRequire(path.join(web, 'package.json'));
const { JSDOM } = requireWeb('jsdom');
const sharp = requireWeb('sharp');
const assets = require('../apps/web/content/articles/interactive-guides/islamic-patterns/assets.json');
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
async function main() {
  if (!process.argv[2]) throw new Error('Provide the original Islamic patterns HTML file.');
  const document = new JSDOM(fs.readFileSync(process.argv[2], 'utf8')).window.document;
  const images = [...document.querySelectorAll('img[src^="data:image/"]')].slice(1).concat([...document.querySelectorAll('svg image')]);
  if (images.length !== assets.length) throw new Error('The source image set differs.');
  for (let i = 0; i < assets.length; i++) {
    const asset = assets[i], value = images[i].getAttribute('src') || images[i].getAttribute('href');
    const original = Buffer.from(value.slice(value.indexOf(',') + 1), 'base64');
    if (sha(original) !== asset.originalSHA256) throw new Error(`Source changed: ${asset.key}`);
    for (const variant of asset.variants) {
      const bytes = await sharp(original).rotate().resize({width: variant.size, height: variant.size, fit:'inside', withoutEnlargement:true}).webp({quality:variant.size === 2400 ? 84 : 78, effort:5}).toBuffer();
      if (sha(bytes) !== variant.sha256) throw new Error(`Encoded image differs: ${variant.url}; check the Sharp/libvips version.`);
      const target = path.join(web, 'public', variant.url);
      fs.mkdirSync(path.dirname(target), {recursive:true}); fs.writeFileSync(target, bytes);
    }
    console.log(`Verified ${asset.key}: three responsive images`);
  }
}
main().catch(error => {console.error(error.message); process.exitCode=1;});
