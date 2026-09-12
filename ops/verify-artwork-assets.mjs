import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";

const root = new URL("../", import.meta.url);
const manifest = JSON.parse(await readFile(new URL("content/artworks/selection-2026-09.json", root), "utf8"));
const paths = new Set();
let total = 0;
for (const work of manifest.artworks) {
  const media = work.media;
  assert.match(media.path, /^\/assets\/artworks\/[a-z0-9-]+\.(jpg|png)$/);
  assert(!paths.has(media.path), "Duplicate asset: " + media.path);
  paths.add(media.path);
  assert.equal(new URL(media.source_url).protocol, "https:");
  assert.equal(new URL(work.source_url).protocol, "https:");
  assert(["public_domain", "cc0"].includes(media.rights_status));
  assert(media.alt.length > 20 && media.credit.length > 20);
  const path = new URL("apps/web/public" + media.path, root);
  const bytes = await readFile(path);
  assert.equal(bytes.length, media.bytes, "Size changed: " + media.path);
  assert.equal(createHash("sha256").update(bytes).digest("hex"), media.sha256, "Checksum changed: " + media.path);
  assert(media.width > 0 && media.height > 0, "Missing dimensions: " + media.path);
  assert(media.mime === "image/png" ? bytes.subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10])) : bytes[0] === 255 && bytes[1] === 216, "Invalid image signature: " + fileURLToPath(path));
  total += bytes.length;
}
console.log(`Verified ${paths.size} local artwork assets for ${new Set(manifest.artworks.map(work => work.artist_slug)).size} painters; ${(total / 1024 / 1024).toFixed(1)} MiB. All checksums match.`);
