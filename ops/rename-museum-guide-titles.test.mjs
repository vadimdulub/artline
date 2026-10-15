import { afterEach, test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
import { prepareRename, sha256, titleFor } from './rename-museum-guide-titles.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const policy = JSON.parse(fs.readFileSync(path.join(root, 'content/curation/museum-guide-titles.json')));
const temporary = [];
afterEach(() => { for (const dir of temporary.splice(0)) fs.rmSync(dir, { recursive: true }); });

function fixture() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'artline-guide-title-test-')); temporary.push(dir);
  const contentRoot = path.join(dir, 'source'), outputRoot = path.join(dir, 'output'), searchIndex = path.join(dir, 'index.json');
  const smallPolicy = { ...policy, locales: ['en', 'ru'], museums: { louvre: ['Louvre', 'Лувр'] } };
  const summary = { slug: 'louvre', museum: 'Louvre', city: 'Paris', country: 'France', title: 'Old English title', subtitle: 'Unchanged subtitle', locales: ['en', 'ru'], count: 1, unknown: { keep: true } };
  const sources = {}, editions = [];
  const write = (name, value) => {
    const raw = JSON.stringify(value, null, 2) + '\n';
    fs.mkdirSync(path.dirname(path.join(contentRoot, name)), { recursive: true }); fs.writeFileSync(path.join(contentRoot, name), raw); sources[name] = sha256(raw);
  };
  write('museum-guides/index.json', [summary]);
  for (const locale of summary.locales) {
    const edition = { ...summary, locale, title: locale === 'en' ? summary.title : 'Старое название', works: [{ id: 'unchanged-work', title: 'Not a guide title', source: 'https://example.org/object' }], unknown: { untouched: true } };
    editions.push(edition); write(`museum-guides/louvre/${locale}.json`, edition);
  }
  const text = [summary.title, summary.subtitle, summary.museum, summary.city, summary.country, ''];
  for (const edition of editions) text.push(...['title', 'subtitle', 'museum', 'city', 'country'].map(key => edition[key]), '');
  const index = { sources, entries: [
    { slug: 'artist', kind: 'artist', title: 'Artist guide untouched', search: 'Artist unchanged', institutions: [] },
    { slug: 'louvre', kind: 'museum', title: summary.title, search: [...new Set(text)].join(' '), institutions: ['louvre'], image: '/same.jpg', count: 1 },
    { slug: 'art-history-timeline', kind: 'using', title: 'Timeline untouched', search: 'Using Artline' },
  ] };
  fs.writeFileSync(searchIndex, JSON.stringify(index));
  return { policy: smallPolicy, contentRoot, outputRoot, searchIndex, dir, index, editions };
}

test('all 86 guides have complete Codex-authored titles in ten languages', () => {
  assert.equal(Object.keys(policy.museums).length, 86); assert.equal(policy.locales.length, 10);
  for (const [slug, names] of Object.entries(policy.museums)) {
    assert.equal(names.length, policy.locales.length);
    for (const locale of policy.locales) {
      const title = titleFor(policy, slug, locale); assert.ok(title.length >= 4); assert.ok(!title.includes('{museum}'));
      if (locale === 'en') assert.equal(title, `Masterpieces for ${names[0]}`);
    }
  }
  assert.equal(titleFor(policy, 'louvre', 'fr'), 'Chefs-d’œuvre : Louvre');
  assert.equal(titleFor(policy, 'louvre', 'ja'), 'ルーヴル美術館の名作');
  assert.equal(titleFor(policy, 'louvre', 'ar'), 'روائع متحف اللوفر');
});

test('unknown locales and incomplete localization rows fail closed', () => {
  assert.throws(() => titleFor(policy, 'louvre', 'xx'), /Unknown locale/);
  assert.throws(() => titleFor(policy, 'unknown', 'en'), /Missing localized names/);
  assert.throws(() => titleFor({ ...policy, museums: { louvre: ['Louvre'] } }, 'louvre', 'en'), /Missing localized names/);
});

test('changes titles and multilingual search while preserving all other content', () => {
  const f = fixture(), source = fs.readFileSync(path.join(f.contentRoot, 'museum-guides/louvre/en.json'));
  const result = prepareRename(f); assert.equal(result.editions, 2); assert.equal(result.changedEditions, 2);
  assert.deepEqual(fs.readFileSync(path.join(f.contentRoot, 'museum-guides/louvre/en.json')), source);
  for (const before of f.editions) {
    const after = JSON.parse(fs.readFileSync(path.join(f.outputRoot, `museum-guides/louvre/${before.locale}.json`)));
    assert.deepEqual({ ...after, title: before.title }, before);
  }
  const next = JSON.parse(fs.readFileSync(path.join(f.outputRoot, 'guide-search-index.json')));
  assert.deepEqual(next.entries.filter(e => e.kind !== 'museum'), f.index.entries.filter(e => e.kind !== 'museum'));
  const entry = next.entries.find(e => e.kind === 'museum');
  assert.equal(entry.title, 'Masterpieces for Louvre'); assert.ok(entry.search.includes('Шедевры: Лувр'));
  assert.ok(!entry.search.includes('Old English title')); assert.ok(!entry.search.includes('Старое название'));
  assert.deepEqual({ ...entry, title: f.index.entries[1].title, search: f.index.entries[1].search }, f.index.entries[1]);
});

test('stale content hashes prevent partial output', () => {
  const f = fixture(); fs.appendFileSync(path.join(f.contentRoot, 'museum-guides/louvre/en.json'), '\n');
  assert.throws(() => prepareRename(f), /Stale search source/); assert.equal(fs.existsSync(f.outputRoot), false);
});

test('missing language coverage prevents partial output', () => {
  const f = fixture(); f.policy = { ...f.policy, locales: ['en'] };
  assert.throws(() => prepareRename(f), /Locale coverage/); assert.equal(fs.existsSync(f.outputRoot), false);
});

test('title transform is idempotent after applying its staged files', () => {
  const f = fixture(); prepareRename(f);
  fs.cpSync(path.join(f.outputRoot, 'museum-guides'), path.join(f.contentRoot, 'museum-guides'), { recursive: true });
  fs.copyFileSync(path.join(f.outputRoot, 'guide-search-index.json'), f.searchIndex);
  const result = prepareRename({ ...f, outputRoot: path.join(f.dir, 'again') });
  assert.equal(result.changedEditions, 0);
  assert.deepEqual(fs.readFileSync(path.join(f.outputRoot, 'guide-search-index.json')), fs.readFileSync(path.join(f.dir, 'again/guide-search-index.json')));
});
