// Bounded anonymous HTTP checks; never writes catalogue data.
// node ops/verify-museum-directory.mjs BASE OUTPUT [baseline|web]
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, writeFile } from 'node:fs/promises';
import { dirname } from 'node:path';

const [base, output, mode = 'api'] = process.argv.slice(2);
assert(base && output, 'BASE and OUTPUT are required');
const prefix = mode === 'web' ? '/api/backend/v1' : '/api/v1';
const cases = [
  ['frans-hals', 'country=NL&q=Frans%20Hals&limit=5', 'wikimedia-museum-q574961'],
  ['folkwang', 'country=DE&q=Folkwang&limit=5', 'wikimedia-museum-q125634'],
  ['dutch', 'country=NL&limit=24'],
  ['german', 'country=DE&limit=24'],
  ['both', 'country=NL&country=DE&limit=5'],
  ['unfiltered', 'limit=24'],
  ['maximum-page', 'limit=60'],
  ['empty', 'q=no-such-museum-audit-20260917&limit=5'],
  ['highlights', 'selection=museum&limit=5'],
  ['owner', 'selection=owner&limit=5'],
  ['on-view', 'display=on_view&limit=5'],
  ['artist', 'artist=rembrandt&limit=5'],
  ['movement', 'movement=impressionism&limit=5'],
  ['work-type', 'country=DE&work_type=painting&limit=5'],
  ['combined', 'country=NL&country=DE&artist=rembrandt&movement=baroque&work_type=painting&limit=5'],
  ['selection-artist', 'selection=museum&artist=rembrandt&limit=5'],
];
const requests = [];
async function check(name, path, validate) {
  const started = performance.now();
  const result = { name, path };
  try {
    const response = await fetch(base + path, { signal: AbortSignal.timeout(25000) });
    result.http_status = response.status;
    const text = await response.text();
    result.payload_sha256 = createHash('sha256').update(text).digest('hex');
    const data = JSON.parse(text);
    assert.equal(response.status, 200);
    validate?.(data);
    result.verified = true;
    result.total = data.total;
    result.items = data.items?.length;
    result.slugs = data.items?.map(item => item.slug);
    result.next_cursor = data.next_cursor;
    return data;
  } catch (error) {
    result.verified = false;
    result.error = error.message;
  } finally {
    result.seconds = +( (performance.now() - started) / 1000 ).toFixed(4);
    requests.push(result);
    console.log(JSON.stringify(result));
  }
}

for (const [name, query, expectedSlug] of mode === 'baseline' ? cases.slice(0, 2) : cases) {
  const params = new URLSearchParams(query);
  const countries = params.getAll('country');
  const validate = data => {
    assert(Array.isArray(data.items));
    assert(Number.isInteger(data.total));
    assert(data.items.length <= Number(params.get('limit')));
    assert(Array.isArray(data.facets.countries));
    assert(Array.isArray(data.facets.movements));
    if (expectedSlug) assert(data.items.some(item => item.slug === expectedSlug));
    if (name === 'empty') assert.equal(data.total, 0);
    for (const item of data.items) {
      assert(item.work_count >= item.holding_count);
      assert(item.work_count >= item.on_view_count);
      if (countries.length) assert(item.venues.some(venue => countries.includes(venue.country)));
    }
  };
  const page = await check(name, `${prefix}/museums?${query}`, validate);
  if (mode !== 'baseline' && name === 'both' && page?.next_cursor) {
    const next = await check('both-next', `${prefix}/museums?${query}&cursor=${encodeURIComponent(page.next_cursor)}`, validate);
    if (next) {
      assert.equal(next.total, page.total);
      assert(!next.items.some(item => page.items.some(previous => previous.id === item.id)));
    }
  }
}
if (mode !== 'baseline') {
  for (let n = 0; n < 6; n++) {
    const [name, query, slug] = cases[n % 2];
    await check(`${name}-repeat-${n}`, `${prefix}/museums?${query}`, data => assert(data.items.some(item => item.slug === slug)));
  }
  for (const [slug, id] of [
    ['the-met', 'aa629199-d198-56be-8db8-289252e0d34a'],
    ['national-gallery-of-art', 'd230bce2-acb0-5484-a504-d1711c95a5c1'],
  ]) {
    await check(`${slug}-artwork`, `${prefix}/museums/${slug}/works/${id}`, data => assert.equal(data.id, id));
  }
}
const failed = requests.filter(result => !result.verified);
await mkdir(dirname(output), { recursive: true });
await writeFile(output, JSON.stringify({ at: new Date().toISOString(), base, mode, anonymous: true, passed: requests.length - failed.length, failed: failed.length, requests }, null, 2) + '\n');
if (failed.length && mode !== 'baseline') process.exitCode = 1;
