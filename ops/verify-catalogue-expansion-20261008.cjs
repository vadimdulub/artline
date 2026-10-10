// Read-only checks against the actual public production routes.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const { chromium, expect, request } = require(path.join(root, 'apps/web/node_modules/@playwright/test'));
const run = path.join(root, 'docs/research/catalogue-expansion-20261008');
const samples = JSON.parse(fs.readFileSync(path.join(run, 'live-check-samples.json'), 'utf8'));
const origin = 'https://artlines.org';
const results = [];
const errors = [];
const bad = /\bin review\b|under review|unverified date|details (?:not available|not recorded)|no details available|source capture|source-backed/i;

(async () => {
 const api = await request.newContext({ baseURL: origin });
 const browser = await chromium.launch({ channel: 'chrome', headless: true });
 try {
  for (const w of samples.artworks) {
   const url = `/api/backend/v1/museums/${w.museum_slug}/works/${w.id}`;
   const response = await api.get(url);
   assert.equal(response.status(), 200, url);
   const actual = await response.json();
   assert.equal(actual.id, w.id);
   assert.equal(actual.title, w.title);
   assert.equal(actual.date_display, w.date_display);
   assert.equal(actual.creation_year_start, w.first);
   assert.equal(actual.creation_year_end, w.last);
   assert.equal(actual.accession_number, w.accession);
   assert.equal(actual.holding.id, w.institution_id);
   assert.equal(actual.status, 'published');
   assert.equal(actual.display, null);
   assert.equal(actual.media_url, null);
   assert.equal(actual.unlinked_creator_label, w.creator_label);
   if (w.artist_id) assert(actual.artists.some(a => a.id === w.artist_id && a.role === w.attribution_role));
   results.push({ check: 'public artwork API', id: w.id, title: w.title, status: 'passed' });
  }
  for (const museum of samples.institutions) {
   const response = await api.get(`/api/backend/v1/museums/${museum.slug}/works?limit=24`);
   assert.equal(response.status(), 200);
   const data = await response.json();
   assert(data.items.length > 0 && data.items.length <= 24);
   results.push({ check: 'bounded museum collection page', slug: museum.slug, status: 'passed' });
  }
  const context = await browser.newContext({ viewport: { width: 1440, height: 1050 } });
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(error.message));
  for (const [i, w] of samples.artworks.entries()) {
   await page.goto(`${origin}/museums/${w.museum_slug}?work=${w.id}`, { waitUntil: 'domcontentloaded' });
   const dialog = page.getByRole('dialog', { name: 'Museum artwork details' });
   await expect(dialog.getByRole('heading', { name: w.title, exact: true })).toBeVisible({ timeout: 30000 });
   const text = await dialog.innerText();
   assert(!bad.test(text), 'Internal placeholder shown for ' + w.title);
   assert(text.includes(w.date_display), 'Source date not visible');
   assert(!/reported on view/i.test(text), 'Unsupported current display');
   if (w.attribution_role === 'attributed_to' && w.artist_id) assert(/attributed to/i.test(text));
   results.push({ check: 'live artwork drawer and known-only metadata', id: w.id, title: w.title, status: 'passed' });
   console.log('Verified live artwork:', w.title);
   if (i === 0) await page.screenshot({ path: '/tmp/artline-expansion-morocco-live.png', fullPage: false });
  }
  for (const artist of samples.artists) {
   await page.goto(`${origin}/artists/${artist.slug}`, { waitUntil: 'domcontentloaded' });
   await expect(page.getByRole('heading', { name: artist.display_name, exact: true }).first()).toBeVisible({ timeout: 30000 });
   const text = await page.locator('body').innerText();
   assert(!bad.test(text), 'Internal placeholder in new artist profile');
   results.push({ check: 'new published artist profile', id: artist.id, name: artist.display_name, status: 'passed' });
   console.log('Verified artist:', artist.display_name);
  }
  await page.screenshot({ path: '/tmp/artline-expansion-artist-live.png', fullPage: false });
  assert.deepEqual(errors, []);
  const result = { at: new Date().toISOString(), origin, checks_passed: results.length, results, browser_errors: errors };
  const output = path.join(run, 'live-verification.json');
  assert(!fs.existsSync(output), 'Preserve existing verification receipt');
  fs.writeFileSync(output, JSON.stringify(result, null, 2));
  console.log(JSON.stringify({ checks_passed: results.length, browser_errors: errors }));
  await context.close();
 } finally { await browser.close(); await api.dispose(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
