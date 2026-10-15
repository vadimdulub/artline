#!/usr/bin/env node
// Read-only verification of a prepared title release. Uses local Poppler tools;
// optionally checks a running preview without requesting external image assets.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';
import { sha256, titleFor } from './rename-museum-guide-titles.mjs';

const exec = promisify(execFile);
const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const [prepared, preview] = process.argv.slice(2);
assert.ok(prepared, 'Usage: node ops/verify-museum-guide-titles.mjs PREPARED [LOCAL_PREVIEW_URL]');
if (preview) assert.ok(['127.0.0.1', 'localhost', '[::1]'].includes(new URL(preview).hostname), 'Use a local preview');
const read = name => JSON.parse(fs.readFileSync(name, 'utf8'));
const content = path.join(repo, 'apps/web/content/articles');
const policy = read(path.join(repo, 'content/curation/museum-guide-titles.json'));
const changes = read(path.join(prepared, 'title-changes.json'));
const beforeIndex = read(path.join(repo, 'apps/server/internal/guides/index.json'));
const afterIndex = read(path.join(prepared, 'guide-search-index.json'));
assert.deepEqual(afterIndex.entries.filter(e => e.kind !== 'museum'), beforeIndex.entries.filter(e => e.kind !== 'museum'));
assert.equal(changes.changes.length, Object.keys(policy.museums).length * policy.locales.length);
assert.equal(new Set(changes.changes.map(c => `${c.slug}/${c.locale}`)).size, changes.changes.length);
const expectedSummaries = read(path.join(content, 'museum-guides/index.json')).map(g => ({ ...g, title: titleFor(policy, g.slug, 'en') }));
assert.deepEqual(read(path.join(prepared, 'museum-guides/index.json')), expectedSummaries);
for (const [name, hash] of Object.entries(afterIndex.sources)) {
  const base = fs.existsSync(path.join(prepared, name)) ? prepared : content;
  assert.equal(sha256(fs.readFileSync(path.join(base, name))), hash, `Search source: ${name}`);
}
for (const entry of afterIndex.entries.filter(e => e.kind === 'museum')) {
  assert.equal(entry.title, titleFor(policy, entry.slug, 'en'));
  for (const locale of policy.locales) assert.ok(entry.search.includes(titleFor(policy, entry.slug, locale)), `Search locale: ${entry.slug}/${locale}`);
  const before = beforeIndex.entries.find(e => e.slug === entry.slug && e.kind === 'museum');
  assert.deepEqual({ ...entry, title: before.title, search: before.search }, before);
}
const escaped = value => value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#x27;');
const report = { museums: expectedSummaries.length, editions: 0, pdfs: 0, htmlPages: 0, pdfPages: 0, pdfBytes: 0, translationAPI: false, databaseWrites: false, artifacts: [] };
let next = 0;
await Promise.all(Array.from({ length: 6 }, async () => {
  for (;;) {
    const row = changes.changes[next++];
    if (!row) return;
    const relative = `museum-guides/${row.slug}/${row.locale}`;
    const before = read(path.join(content, `${relative}.json`));
    const afterRaw = fs.readFileSync(path.join(prepared, `${relative}.json`));
    const after = JSON.parse(afterRaw);
    assert.equal(after.title, titleFor(policy, row.slug, row.locale));
    assert.deepEqual({ ...after, title: before.title }, before, `Non-title change: ${relative}`);
    assert.equal(sha256(afterRaw), row.afterSHA256);
    const pdf = path.join(prepared, `${relative}.pdf`);
    const [{ stdout: info }, { stdout: originalInfo }] = await Promise.all([
      exec('pdfinfo', ['-enc', 'UTF-8', pdf]),
      exec('pdfinfo', ['-enc', 'UTF-8', path.join(content, `${relative}.pdf`)]),
    ]);
    assert.equal(info.match(/^Title:\s+(.+)$/m)?.[1], `${after.title} — Artline`, `PDF title: ${relative}`);
    const pages = Number(info.match(/^Pages:\s+(\d+)$/m)?.[1]);
    assert.ok(pages > 0);
    assert.equal(pages, Number(originalInfo.match(/^Pages:\s+(\d+)$/m)?.[1]), `PDF page count: ${relative}`);
    const pdfRaw = fs.readFileSync(pdf);
    report.artifacts.push({ path: `${relative}.pdf`, sha256: sha256(pdfRaw), bytes: pdfRaw.length, pages });
    report.pdfs++; report.pdfPages += pages; report.pdfBytes += pdfRaw.length; report.editions++;
    if (preview) {
      const route = `/guides/${row.slug}${row.locale === 'en' ? '' : '/' + row.locale}`;
      const response = await fetch(new URL(route, preview), { signal: AbortSignal.timeout(30000) });
      assert.equal(response.status, 200, route);
      const html = await response.text();
      assert.ok(html.includes(`<h1>${escaped(after.title)}</h1>`), `H1: ${route}`);
      assert.ok(html.includes(`<title>${escaped(after.title)} — Artline</title>`), `SEO title: ${route}`);
      assert.ok(html.includes(`property="og:title" content="${escaped(after.title)} — Artline"`), `Open Graph title: ${route}`);
      const articles = [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)].map(m => JSON.parse(m[1]));
      assert.ok(articles.some(a => a['@type'] === 'Article' && a.headline === after.title && a.inLanguage === row.locale), `Structured article: ${route}`);
      report.htmlPages++;
    }
  }
}));
report.artifacts.sort((a, b) => a.path.localeCompare(b.path));
fs.writeFileSync(path.join(prepared, 'verification.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ ...report, artifacts: undefined }, null, 2));
